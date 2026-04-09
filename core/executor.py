"""
执行器 - NanoAgent
管理执行流程的各个阶段
"""
import re
from typing import Dict, Any, Optional
from loguru import logger
from spec.models import AgentPlan, TaskSpec
from core.interfaces import ILLMClient, IRouter, IManifestManager, IContextLoader, ISpecGenerator


class AgentExecutor:
    """执行器 - 管理执行流程"""

    def __init__(
        self,
        llm_client: ILLMClient,
        router: IRouter,
        manifest_manager: IManifestManager,
        context_loader: IContextLoader,
        spec_generator: ISpecGenerator,
        tool_registry: Any = None,
        persistence_manager: Any = None,
        cache: Any = None,
        config: Dict[str, Any] = None
    ):
        """
        初始化执行器

        Args:
            llm_client: LLM 客户端
            router: 路由器
            manifest_manager: Manifest 管理器
            context_loader: 上下文加载器
            spec_generator: Spec 生成器
            tool_registry: 工具注册表
            persistence_manager: 持久化管理器
            cache: 缓存管理器
            config: 配置字典
        """
        self.llm_client = llm_client
        self.router = router
        self.manifest_manager = manifest_manager
        self.context_loader = context_loader
        self.spec_generator = spec_generator
        self.tool_registry = tool_registry
        self.persistence_manager = persistence_manager
        self.cache = cache
        self.config = config or {}
        
        # 从配置中读取参数
        core_config = self.config.get("core", {})
        performance_config = core_config.get("performance", {})
        
        self.max_steps = performance_config.get("max_steps", 20)
        self.max_context_tokens = performance_config.get("max_context_tokens", 3500)
        self.context_window_ratio = performance_config.get("context_window_ratio", 0.7)

    def route_task(self, task: str) -> Dict:
        """
        阶段1：智能路由

        Args:
            task: 用户任务

        Returns:
            路由决策结果
        """
        logger.info("=== Phase 1: Task Routing ===")
        routing_decision = self.router.route(task)
        logger.info(
            "Task routed",
            task_type=routing_decision.task_type.value,
            confidence=f"{routing_decision.confidence:.2%}"
        )
        return routing_decision.model_dump()

    def should_init_spec(self, task: str, routing_decision: Dict) -> bool:
        """
        判断是否需要初始化 Spec

        Args:
            task: 用户任务
            routing_decision: 路由决策

        Returns:
            是否需要初始化
        """
        # 检查是否已存在 manifest
        manifest = self.manifest_manager.load_manifest()
        if manifest is None:
            # 没有 manifest，需要初始化
            return True
        
        # manifest 已存在，不需要重新初始化，支持恢复逻辑
        return False

    def load_context(self) -> Dict:
        """
        阶段3：动态加载上下文

        Returns:
            上下文字典
        """
        logger.info("=== Phase 3: Dynamic Context Loading ===")
        context = self.context_loader.dynamic_load_context()
        logger.info("Context loaded", has_master=bool(context.get("master_spec")))
        return context

    def build_system_prompt(self, context: Dict) -> str:
        """
        构建系统提示（基于当前阶段的约束）

        Args:
            context: 上下文字典

        Returns:
            系统提示
        """
        if context.get("master_spec") and context.get("current_stage_spec"):
            # 规范化约束：支持 list 或 dict 格式
            constraints = context.get("constraints", {})
            if isinstance(constraints, list):
                # 如果是 list，视为 always 约束
                always_constraints = constraints
                never_constraints = []
            elif isinstance(constraints, dict):
                # 如果是 dict，提取 always 和 never
                always_constraints = constraints.get("always", [])
                never_constraints = constraints.get("never", [])
            else:
                # 无效格式，使用默认值
                always_constraints = []
                never_constraints = []
            
            return f"""【当前任务阶段】

## 核心目标（来自 Master Spec）
{context['master_spec'][:300]}

## 当前阶段约束
{context['current_stage_spec']}

## 必须遵守的规则
{chr(10).join(f'- {c}' for c in always_constraints)}

## 禁止的操作
{chr(10).join(f'- {c}' for c in never_constraints)}
"""
        else:
            return "No spec context available"

    def _truncate_context_for_tokens(self, context: str, max_tokens: int = None) -> str:
        """截断上下文以符合 token 限制（简单估算：1 token ≈ 4 字符）"""
        if max_tokens is None:
            max_tokens = self.max_context_tokens
        
        max_chars = max_tokens * 4  # 粗略估算
        
        if len(context) <= max_chars:
            return context
        
        truncated = context[:max_chars]
        logger.warning(f"Context truncated from {len(context)} to {len(truncated)} chars")
        return truncated
    
    def _get_recent_observations_summary(self, observations: list, max_items: int = 5) -> str:
        """获取最近的观察摘要"""
        if not observations:
            return "No observations yet"
        
        recent = observations[-max_items:]
        summary = []
        for i, obs in enumerate(recent, 1):
            raw = obs.get("raw", "")
            summary.append(f"Step {i}: {raw[:100]}...")
        
        return "\n".join(summary)
    
    def planning_phase(self, task: str, context: Dict) -> AgentPlan:
        """
        阶段4：Planning 阶段

        Args:
            task: 用户任务
            context: 上下文字典

        Returns:
            执行计划
        """
        logger.info("=== Planning Phase ===")
        
        if context is None:
            context = {}
        
        # 构建动态 Spec 内容（基于当前阶段）
        if context.get("master_spec") and context.get("current_stage_spec"):
            full_spec_content = f"""【当前任务阶段】

## 核心目标（来自 Master Spec）
{context['master_spec'][:300]}

## 当前阶段约束
{context['current_stage_spec']}

## 必须遵守的规则
{chr(10).join(f'- {c}' for c in context.get('constraints', {}).get('always', []))}

## 禁止的操作
{chr(10).join(f'- {c}' for c in context.get('constraints', {}).get('never', []))}
"""
        else:
            # 回退到旧方式
            full_spec_content = "No spec context available"
        
        from core.prompt import SYSTEM_PROMPT, PLANNING_PROMPT
        from spec.models import AgentPlan, PlanStep
        import json
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": PLANNING_PROMPT.format(
                task_description=task,
                task_spec=full_spec_content,
                current_context="",
                available_tools=self.tool_registry.get_tool_descriptions() if self.tool_registry else "No tools available"
            )}
        ]
        
        try:
            # 尝试使用结构化输出（更可靠）
            plan = self.llm_client.structured_chat(messages, AgentPlan, temperature=0.5)
            logger.info(f"Plan generated with {len(plan.steps)} steps")
            return plan
            
        except Exception as e:
            logger.warning(f"Structured planning failed, falling back to JSON parsing: {e}")
            # 回退到 JSON 解析
            try:
                response = self.llm_client.chat(messages, temperature=0.5)
                plan_data = json.loads(response)
                plan = AgentPlan(
                    steps=[
                        PlanStep(
                            step_id=step["step_id"],
                            goal=step["goal"],
                            suggested_tools=step.get("tool", "").split(",")
                        )
                        for step in plan_data.get("steps", [])
                    ],
                    overall_goal=plan_data.get("overview", "")
                )
                logger.info(f"Plan generated with {len(plan.steps)} steps (fallback)")
                return plan
            except Exception as e2:
                logger.error(f"Planning error: {e2}")
                # 生成简单计划作为回退
                return AgentPlan(
                    steps=[PlanStep(step_id=1, goal="Execute task", suggested_tools=[])],
                    overall_goal="Fallback plan"
                )

    def think_phase(self, task: str, context: Dict, observations: list, step_count: int = 0, spec: Any = None) -> Dict:
        """
        Think 阶段：分析当前状态

        Args:
            task: 用户任务
            context: 上下文字典
            observations: 历史观察
            step_count: 当前步数
            spec: 任务规范

        Returns:
            思考结果（包含 action 和参数）
        """
        logger.info(f"=== Think Phase (Step {step_count + 1}) ===")
        
        if context is None:
            context = {}
        
        # 使用摘要而不是完整的观察记录
        recent_observations = self._get_recent_observations_summary(observations, max_items=3)
        
        from core.prompt import SYSTEM_PROMPT, REACT_THINK_PROMPT
        import json
        
        # 构建动态提示
        prompt = REACT_THINK_PROMPT.format(
            current_step=step_count + 1,
            completed_steps=[s.get("step", 0) for s in observations],
            step_count=step_count,
            max_steps=self.max_steps,
            task_goal=spec.overall_goal if spec else task,
            recent_observations=recent_observations,
            available_tools=self.tool_registry.get_tool_descriptions() if self.tool_registry else "No tools available"
        )
        
        # 添加当前阶段约束
        if context.get("current_stage_spec"):
            prompt += "\n\n【当前阶段约束】\n"
            prompt += context["current_stage_spec"]
        
        if context.get("constraints"):
            constraints = context["constraints"]
            if constraints.get("never"):
                prompt += "\n【禁止操作】\n"
                for c in constraints["never"]:
                    prompt += f"- {c}\n"
        
        # 截断 prompt 以符合 token 限制
        prompt = self._truncate_context_for_tokens(prompt)
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm_client.chat(messages, temperature=0.7)
        
        logger.debug(f"Think response: {response[:200]}...")
        
        # 解析决策
        if "TASK_COMPLETE" in response:
            return {"action": "complete", "reason": "Task completed"}
        elif "WAIT_FOR_USER" in response:
            return {"action": "wait", "reason": "Needs user input"}
        elif "STAGE_COMPLETE" in response:
            # 提取决策和交付物
            decisions = []
            artifacts = []
            
            try:
                start = response.find("{")
                end = response.rfind("}") + 1
                if start != -1 and end > start:
                    stage_data = json.loads(response[start:end])
                    decisions = stage_data.get("decisions", [])
                    artifacts = stage_data.get("artifacts", [])
            except Exception as e:
                logger.error(f"Failed to parse STAGE_COMPLETE JSON: {e}", exc_info=True)
                logger.debug(f"Response substring: {response[max(0, start-50):min(len(response), end+50)] if start != -1 else response[:100]}")
            
            return {
                "action": "stage_complete",
                "stage_id": context.get("current_stage_id", "unknown"),
                "decisions": decisions,
                "artifacts": artifacts
            }
        else:
            # 解析工具调用
            try:
                # 尝试解析 JSON 格式的工具调用
                if "{" in response and "}" in response:
                    start = response.find("{")
                    end = response.rfind("}") + 1
                    action_data = json.loads(response[start:end])
                    
                    if "tool" in action_data or "function" in action_data:
                        tool_name = action_data.get("tool") or action_data.get("function")
                        arguments = action_data.get("arguments", action_data.get("parameters", {}))
                        return {
                            "action": "tool_call",
                            "tool": tool_name,
                            "arguments": arguments,
                            "thought": action_data.get("thought", "")
                        }
                
                # 回退：基于文本解析
                return {
                    "action": "tool_call",
                    "tool": "unknown",
                    "arguments": {},
                    "thought": response[:200]
                }
                
            except Exception as e:
                logger.error(f"Failed to parse think response: {e}")
                return {"action": "continue", "thought": response[:200]}

    def act_phase(self, action: Dict) -> Any:
        """
        Act 阶段：执行动作

        Args:
            action: 动作描述

        Returns:
            执行结果
        """
        if action["action"] == "tool_call":
            logger.info(f"Executing tool: {action['tool']}")
            
            tool_name = action["tool"]
            arguments = action.get("arguments", {}).copy()
            
            # 检查是否为 HITL 工具
            from core.tools.hitl import HITL_TOOL_NAMES
            if tool_name in HITL_TOOL_NAMES:
                # HITL 工具需要动态加载
                if self.tool_registry:
                    self.tool_registry.load_hitl_tools_on_demand()
            
            # 参数映射：处理常见的参数名差异
            # 为 write_file 映射参数
            if tool_name == "write_file":
                if "path" in arguments and "filepath" not in arguments:
                    arguments["filepath"] = arguments.pop("path")
                    logger.info(f"Mapped 'path' to 'filepath' for write_file")
                elif "file_path" in arguments and "filepath" not in arguments:
                    arguments["filepath"] = arguments.pop("file_path")
                    logger.info(f"Mapped 'file_path' to 'filepath' for write_file")
            
            # 为 read_file 映射参数
            elif tool_name == "read_file":
                if "path" in arguments and "filepath" not in arguments:
                    arguments["filepath"] = arguments.pop("path")
                    logger.info(f"Mapped 'path' to 'filepath' for read_file")
                elif "file_path" in arguments and "filepath" not in arguments:
                    arguments["filepath"] = arguments.pop("file_path")
                    logger.info(f"Mapped 'file_path' to 'filepath' for read_file")
            
            result = self.tool_registry.execute(tool_name, arguments) if self.tool_registry else f"Tool registry not available: {tool_name}"
            
            return result
        else:
            # 内容输出
            content = action.get("content", "No action taken")
            return content

    def observe_phase(self, action: Dict, result: Any) -> Dict:
        """
        Observe 阶段：观察执行结果

        Args:
            action: 执行的动作
            result: 执行结果

        Returns:
            观察结果
        """
        logger.info("=== Observe Phase ===")
        
        # 截断工具结果以减少 token 使用
        tool_result_str = str(result)[:500]
        
        from core.prompt import SYSTEM_PROMPT, REACT_OBSERVE_PROMPT
        import json
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": REACT_OBSERVE_PROMPT.format(
                last_action=json.dumps(action, indent=2),
                tool_result=tool_result_str,
            )}
        ]
        
        try:
            response = self.llm_client.chat(messages, temperature=0.7)
            
            # 检查是否为 HITL 交互
            if "user_answer" in response.lower() or "user input" in response.lower():
                return {
                    "raw": response,
                    "summary": "User interaction needed",
                    "user_answer": response
                }
            
            return {
                "raw": response,
                "summary": response[:200] if len(response) > 200 else response
            }
            
        except Exception as e:
            logger.error(f"Observe phase error: {e}")
            return {
                "raw": f"Error during observation: {str(e)}",
                "summary": "Observation failed"
            }

    def reflection_phase(self, observations: list, spec: Any = None) -> Dict:
        """
        反思阶段：评估执行状态

        Args:
            observations: 观察历史
            spec: 任务规范

        Returns:
            反思结果
        """
        logger.info("=== Reflection Phase ===")
        
        # 使用摘要而不是完整的执行历史
        execution_summary = self._get_recent_observations_summary(observations, max_items=10)
        
        # 处理 spec 可能为 None 的情况
        task_spec_json = spec.model_dump_json(indent=2) if spec else "{}"
        
        from core.prompt import SYSTEM_PROMPT, REFLECTION_PROMPT
        from pydantic import BaseModel, Field
        from typing import List
        import json
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": REFLECTION_PROMPT.format(
                execution_history=execution_summary,
                task_spec=task_spec_json,
                current_progress=f"{len(observations)} steps completed"
            )}
        ]
        
        # 截断 prompt 以符合 token 限制
        user_content = messages[1]["content"]
        messages[1]["content"] = self._truncate_context_for_tokens(user_content)
        
        try:
            # 尝试使用结构化输出
            class ReflectionResult(BaseModel):
                task_completed: bool
                progress_summary: str
                issues_found: List[str] = Field(default_factory=list)
                solutions_applied: List[str] = Field(default_factory=list)
                next_action: str
                confidence_score: float = 0.5
            
            reflection = self.llm_client.structured_chat(messages, ReflectionResult, temperature=0.5)
            logger.info(f"Reflection: {reflection.next_action}")
            return reflection.model_dump()
            
        except Exception as e:
            logger.warning(f"Structured reflection failed, falling back to JSON parsing: {e}")
            # 回退到 JSON 解析
            try:
                response = self.llm_client.chat(messages, temperature=0.5)
                reflection = json.loads(response)
                logger.info(f"Reflection: {reflection.get('next_action', 'unknown')}")
                return reflection
            except Exception as e:
                logger.warning(f"Structured reflection failed, falling back to continue: {e}")
                return {"task_completed": False, "next_action": "continue"}

    def check_completion(self, observations: list, manifest) -> bool:
        """
        检查任务是否完成

        Args:
            observations: 观察历史
            manifest: Manifest 对象

        Returns:
            是否完成
        """
        # 简化版：总是返回 False
        return False

    def extract_decisions(self, observations: list) -> list:
        """
        提取决策

        Args:
            observations: 观察历史

        Returns:
            决策列表
        """
        return []

    def init_spec(self, task: str, routing_decision: Dict, spec_initializer: Any = None) -> Any:
        """
        初始化Spec

        Args:
            task: 用户任务
            routing_decision: 路由决策
            spec_initializer: Spec初始化器

        Returns:
            Manifest对象
        """
        if not spec_initializer:
            logger.warning("No spec_initializer provided, skipping spec initialization")
            return None
        
        # 创建简单的 routing_decision 对象
        from spec.models import RoutingDecision
        rd = RoutingDecision(**routing_decision)
        manifest = spec_initializer.init_spec(task, rd)
        
        logger.info(f"Spec initialized: {manifest.project_name if manifest else 'Failed'}")
        return manifest
    
    def load_existing_manifest(self) -> Any:
        """
        加载现有manifest

        Returns:
            Manifest对象，如果不存在则返回None
        """
        manifest = self.manifest_manager.load_manifest()
        if manifest:
            logger.info(f"Loaded existing manifest: {manifest.project_name}")
        return manifest
    
    def save_execution_result(self, decisions: list, artifacts: list) -> None:
        """
        保存执行结果

        Args:
            decisions: 决策列表
            artifacts: 交付物列表
        """
        if self.persistence_manager:
            try:
                result = {
                    "decisions": decisions,
                    "artifacts": artifacts,
                    "timestamp": self._get_timestamp()
                }
                # 这里可以根据需要实现具体的保存逻辑
                logger.info(f"Saved execution result: {len(decisions)} decisions, {len(artifacts)} artifacts")
            except Exception as e:
                logger.error(f"Failed to save execution result: {e}")
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def extract_artifacts(self, observations: list) -> list:
        """
        提取交付物

        Args:
            observations: 观察历史

        Returns:
            交付物文件列表
        """
        artifact_files = []
        for obs in observations:
            raw = obs.get("raw", "")
            match = re.search(r'Successfully wrote \d+ chars to (\S+)', raw)
            if match:
                artifact_files.append(match.group(1))
        return artifact_files