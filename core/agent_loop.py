from loguru import logger
from typing import Dict, List, Any, Optional
import json
from .llm_client import NanoLLMClient
from .agent_state import AgentState, AgentPlan, PlanStep
from .prompt import (
    SYSTEM_PROMPT, PLANNING_PROMPT, REACT_THINK_PROMPT, 
    REACT_OBSERVE_PROMPT, REFLECTION_PROMPT, SELF_CHECK_PROMPT,
    ERROR_RECOVERY_PROMPT, HUMAN_REQUEST_PROMPT
)
from spec.base import TaskSpec
from .router import HybridRouter, RoutingDecision
from .spec_initializer import SpecInitializer
from .manifest_manager import ManifestManager
from .tools import get_tool_registry, CATEGORIES
from .tools.hitl import HITL_TOOL_NAMES
from spec.context import ContextLoader
from spec.generator import SpecGenerator
from .persistence import PersistenceManager
from .container import DIContainer
from .interfaces import ILLMClient, IRouter, IManifestManager, IContextLoader, ISpecGenerator, IPersistenceManager
from core.cache import CacheManager
from .executor import AgentExecutor

class ToolRegistry:
    """工具注册表 - 使用动态加载架构"""
    
    def __init__(self):
        # 使用内部注册表（不是全局的）
        self._internal_registry = get_tool_registry()
        self._loaded_tools: Dict[str, Dict[str, Any]] = {}
    
    def _ensure_tool_loaded(self, name: str) -> None:
        """确保工具已加载（按需加载）"""
        if name in self._loaded_tools:
            return
        
        # 从内部注册表获取工具
        tool = self._internal_registry.get_tool(name)
        if tool:
            self._loaded_tools[name] = tool
            logger.info(f"Loaded tool on-demand: {name}")
        else:
            logger.warning(f"Tool not found: {name}")
    
    def execute(self, name: str, arguments: Dict) -> Any:
        """执行工具"""
        self._ensure_tool_loaded(name)
        
        if name not in self._loaded_tools:
            raise ValueError(f"Tool not found: {name}")
        
        tool = self._loaded_tools[name]
        try:
            result = tool["function"](**arguments)
            logger.info(f"Executed tool {name}: {result[:100] if isinstance(result, str) else 'OK'}")
            return result
        except Exception as e:
            logger.error(f"Tool execution error {name}: {e}")
            return f"Error: {str(e)}"
    
    def get_tool_schemas(self) -> List[Dict]:
        """获取工具的 OpenAI 格式 schema（只返回已加载的工具）"""
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["schema"]
                }
            }
            for name, tool in self._loaded_tools.items()
        ]
    
    def get_tool_descriptions(self) -> str:
        """获取工具描述文本（使用类别索引 + 已加载工具的详情）"""
        # 第一层：类别索引（始终加载）
        category_desc = "\n".join(
            f"- {cat}: {desc}"
            for cat, desc in CATEGORIES.items()
        )
        
        # 第二层：已加载工具的详情
        tool_details = []
        for name, tool in self._loaded_tools.items():
            desc = f"  • {name}: {tool['description']}"
            tool_details.append(desc)
        
        if tool_details:
            return f"工具类别：\n{category_desc}\n\n已加载工具：\n" + "\n".join(tool_details)
        else:
            return f"工具类别（按需加载）：\n{category_desc}"

class NanoAgent:
    """基于 Planning + ReAct 范式的 AI Agent"""
    
    def __init__(self, model: str = "openai/qwen3.5-plus", max_steps: int = 20, max_context_tokens: int = 3500, container: Optional[DIContainer] = None):
        """
        初始化 NanoAgent

        Args:
            model: LLM 模型名称
            max_steps: 最大执行步数
            max_context_tokens: 最大上下文 token 数
            container: 依赖注入容器（可选），如果不提供则使用传统初始化方式
        """
        self.max_steps = max_steps
        self.max_context_tokens = max_context_tokens  # 最大上下文 token 限制（留有余量）
        self.state = AgentState()
        self.spec: Optional[TaskSpec] = None
        self.manifest = None
        self.current_stage_context = {}

        # 使用依赖注入或传统初始化方式
        if container is not None:
            # 使用依赖注入
            self.llm = container.get(ILLMClient)
            self.router = container.get(IRouter)
            self.manifest_manager = container.get(IManifestManager)
            self.context_loader = container.get(IContextLoader)
            self.spec_generator = container.get(ISpecGenerator)
            self.persistence_manager = container.get(IPersistenceManager)
            self.tools = container.get(ToolRegistry)  # 使用本地的 ToolRegistry 类
            self.cache_manager = container.get(CacheManager) if container.has(CacheManager) else None
            self.spec_initializer = SpecInitializer()
            logger.info("NanoAgent initialized with dependency injection")
        else:
            # 传统初始化方式（向后兼容）
            self.llm = NanoLLMClient(model)
            self.router = HybridRouter(self.llm)
            self.spec_initializer = SpecInitializer()
            self.manifest_manager = ManifestManager()
            self.context_loader = ContextLoader(self.manifest_manager)
            self.spec_generator = SpecGenerator(self.llm)
            self.persistence_manager = PersistenceManager()
            self.tools = ToolRegistry()
            self.cache_manager = None  # 传统方式不使用缓存
            
            logger.info("NanoAgent initialized with Spec-Driven and Dynamic Tool Loading")

        # 创建执行器
        self.executor = AgentExecutor(
            llm_client=self.llm,
            router=self.router,
            manifest_manager=self.manifest_manager,
            context_loader=self.context_loader,
            spec_generator=self.spec_generator,
            cache=self.cache_manager,
            max_steps=max_steps
        )

        # 预加载文件工具（常用工具）
        self._preload_file_tools()

        logger.add("nanoagent.log", rotation="10 MB")
    
    def _preload_file_tools(self):
        """预加载文件操作工具（常用）"""
        try:
            # 触发 file 类别的加载
            file_tools = self.tools._internal_registry.get_all_tools("file")
            for tool_name, tool_info in file_tools.items():
                self.tools._loaded_tools[tool_name] = tool_info
            logger.info(f"✓ Preloaded file tools: {list(file_tools.keys())}")
        except Exception as e:
            logger.error(f"Failed to preload file tools: {e}")
    
    def _load_hitl_tools_on_demand(self):
        """按需加载 HITL 工具（动态加载）"""
        try:
            # 触发 hitl 类别的加载
            hitl_tools = self.tools._internal_registry.get_all_tools("hitl")
            for tool_name, tool_info in hitl_tools.items():
                self.tools._loaded_tools[tool_name] = tool_info
            logger.info(f"✓ Loaded HITL tools on-demand: {list(hitl_tools.keys())}")
        except Exception as e:
            logger.error(f"Failed to load HITL tools: {e}")
    
    def _should_init_spec(self, task: str, routing_decision: RoutingDecision) -> bool:
        """判断是否需要初始化 Spec"""
        # 1. 检查是否为复杂任务
        if routing_decision.task_type.value in ["code", "writing", "analyze"]:
            # 2. 检查是否已存在 manifest
            manifest = self.manifest_manager.load_manifest()
            if manifest is None:
                return True
            
            # 3. 检查任务类型是否匹配
            # 简化：暂时总是返回 True，让用户决定
            return True
        
        return False
    
    
    
    def _detect_requirement_change(self, new_input: str) -> bool:
        """检测需求变更"""
        if not self.current_stage_context:
            return False
        
        # 简化版：检查关键词
        stage_spec = self.current_stage_context.get("current_stage_spec", "")
        
        # 如果新输入中包含当前阶段不相关的关键词
        # 这里可以使用更复杂的语义匹配
        # 简化版：总是返回 False，让 LLM 自己判断
        return False
    
    def _prompt_for_spec_update(self) -> str:
        """提示用户更新 Spec"""
        return """⚠️ 检测到需求变更

当前正在执行的任务可能与新的需求不一致。

选项：
1. 继续当前任务
2. 挂起当前任务并更新 Spec
3. 放弃当前任务，开始新任务

请选择下一步操作。"""
    
    def _build_stage_system_prompt(self, context: Dict) -> str:
        """构建阶段特定的系统提示（动态加载核心）"""
        prompt = SYSTEM_PROMPT + "\n\n"
        
        # 添加 master_spec 核心信息
        if context.get("master_spec"):
            prompt += "【Master Spec - 核心方向】\n"
            prompt += context["master_spec"][:500] + "\n\n"  # 限制长度
        
        # 添加当前阶段详细约束
        if context.get("current_stage_spec"):
            prompt += "【当前阶段 - 详细约束】\n"
            prompt += context["current_stage_spec"] + "\n\n"
        
        # 添加约束列表
        constraints = context.get("constraints", {})
        if constraints.get("always"):
            prompt += "【必须遵守】\n"
            for c in constraints["always"]:
                prompt += f"- {c}\n"
            prompt += "\n"
        
        if constraints.get("never"):
            prompt += "【绝对禁止】\n"
            for c in constraints["never"]:
                prompt += f"- {c}\n"
            prompt += "\n"
        
        return prompt
    
    def _extract_decisions(self) -> List[str]:
        """从执行历史中提取关键决策"""
        decisions = []
        
        # 从观察中提取写入的文件
        for obs in self.state.observations:
            if "Successfully wrote" in obs.get("raw", ""):
                # 提取文件名作为决策记录
                import re
                match = re.search(r'Successfully wrote \d+ chars to (\S+)', obs.get("raw", ""))
                if match:
                    decisions.append(f"创建文件: {match.group(1)}")
        
        # 从最近的思考中提取关键信息
        if self.state.observations:
            last_obs = self.state.observations[-1]
            last_think = last_obs.get("raw", "")
            
            # 简单提取：查找包含关键决策的行
            for line in last_think.split('\n'):
                if any(keyword in line.lower() for keyword in ['决定', '选择', '确定', '选定', '使用', '采用']):
                    decisions.append(line.strip())
                    if len(decisions) >= 5:  # 最多保留 5 个决策
                        break
        
        return decisions[:5] if decisions else ["任务完成，关键信息已记录"]
    
    def _on_stage_complete(self, stage_id: str, decisions: List[str], artifacts: List[str]):
        """处理阶段完成（回填和切换）"""
        print(f"\n{'='*60}")
        print(f"✓ 阶段完成: {stage_id}")
        print(f"{'='*60}\n")
        
        if not self.manifest:
            logger.warning("No manifest, skipping stage complete")
            return
        
        # 调用 Manifest 管理器进行回填
        try:
            manifest = self.manifest_manager.sync_and_backfill(
                stage_id=stage_id,
                decisions=decisions,
                completed_artifacts=artifacts,
                next_stage=True
            )
            
            # 显示进度条
            progress = self.manifest_manager.get_progress_bar()
            print(f"📊 进度: {progress}\n")
            
            # 显示下一阶段
            next_stage = self.manifest_manager.get_current_stage()
            if next_stage:
                print(f"➡️  下一阶段: {next_stage}\n")
        except ValueError as e:
            logger.error(f"Stage complete failed: {e}", exc_info=True)
    
    def _generate_spec(self, task: str) -> TaskSpec:
        """根据用户任务生成高质量 Spec（使用模板系统）"""
        return self.spec_generator.generate_spec(task)
    
    def _planning_phase(self, task: str, context: Dict = None) -> AgentPlan:
        """规划阶段：生成执行计划（带动态上下文）"""
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
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": PLANNING_PROMPT.format(
                task_description=task,
                task_spec=full_spec_content,
                current_context="",
                available_tools=self.tools.get_tool_descriptions()
            )}
        ]
        
        try:
            # 尝试使用结构化输出（更可靠）
            plan = self.llm.structured_chat(messages, AgentPlan, temperature=0.5)
            self.state.current_plan = plan
            logger.info(f"Plan generated with {len(plan.steps)} steps")
            return plan
            
        except Exception as e:
            logger.warning(f"Structured planning failed, falling back to JSON parsing: {e}")
            # 回退到 JSON 解析
            try:
                response = self.llm.chat(messages, temperature=0.5)
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
                self.state.current_plan = plan
                logger.info(f"Plan generated with {len(plan.steps)} steps (fallback)")
                return plan
            except Exception as e2:
                logger.error(f"Planning error: {e2}")
                # 生成简单计划作为回退
                return AgentPlan(
                    steps=[PlanStep(step_id=1, goal="Execute task", suggested_tools=[])],
                    overall_goal="Fallback plan"
                )
    
    def _truncate_context_for_tokens(self, context: str, max_tokens: int = None) -> str:
        """截断上下文以符合 token 限制（简单估算：1 token ≈ 4 字符）"""
        if max_tokens is None:
            max_tokens = self.max_context_tokens
        
        max_chars = max_tokens * 4  # 粗略估算
        
        if len(context) <= max_chars:
            return context
        
        # 截断并添加提示
        truncated = context[:max_chars - 100] + "\n\n... [Context truncated due to token limit] ..."
        logger.warning(f"Context truncated from {len(context)} to {len(truncated)} chars")
        return truncated
    
    def _get_recent_observations_summary(self, max_items: int = 5) -> str:
        """获取最近的观察摘要（用于减少 token 使用）"""
        recent = self.state.observations[-max_items:] if self.state.observations else []
        
        if not recent:
            return "No observations yet"
        
        summary_parts = []
        for obs in recent:
            step = obs.get("step", 0)
            action = obs.get("action", {}).get("action", "unknown")
            result = str(obs.get("result", ""))[:200]  # 截断结果

            # 特殊标记 HITL 工具的用户回答
            if obs.get("user_provided_info"):
                summary_parts.append(f"Step {step}: ✓ 用户已回答 ({action}): {result}")
            else:
                summary_parts.append(f"Step {step}: {action} -> {result}")

        return "\n".join(summary_parts)
    
    def _react_think(self, task: str, context: Dict = None) -> Dict:
        """ReAct 循环 - Think 阶段（带动态上下文 + CLI 显示）"""
        logger.info(f"=== Think Phase (Step {self.state.step_count + 1}) ===")
        
        # 获取 CLI 实例
        from cli_interface import get_cli
        cli = get_cli()
        
        if context is None:
            context = {}
        
        # 使用摘要而不是完整的观察记录
        recent_observations = self._get_recent_observations_summary(max_items=3)
        
        # 构建动态提示
        prompt = REACT_THINK_PROMPT.format(
            current_step=self.state.step_count + 1,
            completed_steps=[s.get("step", 0) for s in self.state.observations],
            step_count=self.state.step_count,
            max_steps=self.max_steps,
            task_goal=self.spec.overall_goal if self.spec else task,
            recent_observations=recent_observations,
            available_tools=self.tools.get_tool_descriptions()
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
        
        # 显示思考开始
        cli.display_thinking("正在分析任务...")
        
        response = self.llm.chat(messages, temperature=0.7)
        
        # 显示思考结果（截断）
        cli.display_result(f"思考完成 (长度: {len(response)} 字符)", True)
        
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
                "stage_id": self.manifest.current_stage if self.manifest else "unknown",
                "decisions": decisions,
                "artifacts": artifacts
            }
        else:
            # 尝试解析工具调用
            try:
                # 提取 JSON
                start = response.find("{")
                end = response.rfind("}") + 1
                if start != -1 and end > start:
                    tool_call = json.loads(response[start:end])
                    return {"action": "tool_call", **tool_call}
            except:
                pass
            
            return {"action": "think", "content": response}
    
    def _react_act(self, action: Dict) -> Any:
        """ReAct 循环 - Act 阶段（带 CLI 显示）"""
        # 获取 CLI 实例
        from cli_interface import get_cli
        cli = get_cli()
        
        if action["action"] == "tool_call":
            logger.info(f"Executing tool: {action['tool']}")
            
            # 显示工具调用
            tool_name = action["tool"]
            arguments = action.get("arguments", {}).copy()
            
            # 检查是否为 HITL 工具
            if tool_name in HITL_TOOL_NAMES:
                # HITL 工具显示
                cli.display_action("tool_call", f"HITL 工具: {tool_name}")
                self._load_hitl_tools_on_demand()
            else:
                # 常规工具显示
                arg_preview = f"参数: {list(arguments.keys())[:3]}" if arguments else "无参数"
                cli.display_action("tool_call", f"{tool_name} ({arg_preview})")
            
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
            
            result = self.tools.execute(tool_name, arguments)
            
            # 显示结果
            if "Successfully" in str(result) or result.startswith("✅"):
                cli.display_result(str(result)[:100], True)
            elif "Error" in str(result) or result.startswith("❌"):
                cli.display_error(str(result)[:100])
            else:
                cli.display_result(str(result)[:100], True)
            
            return result
        else:
            # 内容输出
            content = action.get("content", "No action taken")
            cli.display_action("content", content[:100])
            return content
    
    def _react_observe(self, action: Dict, result: Any) -> Dict:
        """ReAct 循环 - Observe 阶段（带 CLI 显示）"""
        logger.info("=== Observe Phase ===")
        
        # 显示观察阶段
        from cli_interface import get_cli
        cli = get_cli()
        cli.display_thinking("观察执行结果...")
        
        # 截断工具结果以减少 token 使用
        tool_result_str = str(result)[:500]
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": REACT_OBSERVE_PROMPT.format(
                last_action=json.dumps(action, indent=2),
                tool_result=tool_result_str,
            )}
        ]
        
        # 截断 prompt 以符合 token 限制
        user_content = messages[1]["content"]
        messages[1]["content"] = self._truncate_context_for_tokens(user_content)
        
        # 使用普通 chat()（不需要流式，因为这是内部调用）
        response = self.llm.chat(messages, temperature=0.7)
        
        # 记录观察（截断结果和分析）
        obs_entry = {
            "step": self.state.step_count,
            "action": action,
            "result": tool_result_str,
            "analysis": response[:200]
        }

        # 特殊处理 HITL 工具的用户回答，标记为已获取信息
        if action.get("action") == "tool_call" and action.get("tool") in ["ask_user_question", "collect_human_feedback"]:
            obs_entry["user_provided_info"] = True
            obs_entry["info_type"] = "user_answer"
            logger.info(f"✓ Recorded user answer in observation for step {self.state.step_count}")

        self.state.observations.append(obs_entry)
        
        return {"analysis": response}
    
    def _reflection_phase(self) -> Dict:
        """反思阶段：评估执行状态"""
        logger.info("=== Reflection Phase ===")
        
        # 使用摘要而不是完整的执行历史
        execution_summary = self._get_recent_observations_summary(max_items=10)
        
        # 处理 spec 可能为 None 的情况
        task_spec_json = self.spec.model_dump_json(indent=2) if self.spec else "{}"
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": REFLECTION_PROMPT.format(
                execution_history=execution_summary,
                task_spec=task_spec_json,
                current_progress=f"{len(self.state.observations)} steps completed"
            )}
        ]
        
        # 截断 prompt 以符合 token 限制
        user_content = messages[1]["content"]
        messages[1]["content"] = self._truncate_context_for_tokens(user_content)
        
        try:
            # 尝试使用结构化输出
            from pydantic import BaseModel, Field
            from typing import List
            
            class ReflectionResult(BaseModel):
                task_completed: bool
                progress_summary: str
                issues_found: List[str] = Field(default_factory=list)
                solutions_applied: List[str] = Field(default_factory=list)
                next_action: str
                confidence_score: float = 0.5
            
            reflection = self.llm.structured_chat(messages, ReflectionResult, temperature=0.5)
            logger.info(f"Reflection: {reflection.next_action}")
            return reflection.model_dump()
            
        except Exception as e:
            logger.warning(f"Structured reflection failed, falling back to JSON parsing: {e}")
            # 回退到 JSON 解析
            try:
                response = self.llm.chat(messages, temperature=0.5)
                reflection = json.loads(response)
                logger.info(f"Reflection: {reflection.get('next_action', 'unknown')}")
                return reflection
            except Exception as e:
                logger.warning(f"Structured reflection failed, falling back to continue: {e}")
                return {"task_completed": False, "next_action": "continue"}
    
    def run(self, task: str) -> Dict:
    
            """执行完整的 Planning + ReAct 循环（集成 Spec-Driven 架构）"""
    
    
    
            # 初始化 CLI
    
            from cli_interface import get_cli
    
            cli = get_cli()
    
            cli.display_header()
    
    
    
            logger.info("=== Starting new task ===", task=task[:100])
    
    
    
            # === 阶段 1：智能路由 ===
    
            cli.display_phase("任务分析")
    
            routing_decision = self.executor.route_task(task)
    
            cli.display_result(f"任务类型: {routing_decision['task_type']}", True)
    
            cli.display_result(f"置信度: {routing_decision['confidence']:.2%}", True)
    
    
    
            # === 阶段 2：Spec 初始化（如果需要） ===
    
            if self.executor.should_init_spec(task, routing_decision):
    
                cli.display_phase("Spec 初始化")
    
                # 创建简单的 routing_decision 对象
    
                from spec.models import RoutingDecision
    
                rd = RoutingDecision(**routing_decision)
    
                self.manifest = self.spec_initializer.init_spec(task, rd)
    
    
    
                # 展示 Spec 概要
    
                print(f"\n📋 Spec 概要")
    
                print(f"{'='*60}")
    
                print(f"项目名称: {self.manifest.project_name}")
    
                print(f"当前阶段: {self.manifest.current_stage}")
    
                print(f"总阶段数: {len(self.manifest.pipeline)}")
    
                print(f"{'='*60}\n")
    
            else:
    
                # 加载现有 manifest
    
                self.manifest = self.manifest_manager.load_manifest()
    
                if self.manifest:
    
                    cli.display_result(f"加载现有 Spec: {self.manifest.project_name}", True)
    
    
    
            # === 阶段 3：动态加载上下文 ===
    
            context = self.executor.load_context()
    
            system_prompt = self.executor.build_system_prompt(context)
    
            self.state.add_message("system", system_prompt)
    
    
    
            # === 阶段 4：Planning 阶段 ===
    
            cli.display_phase("Planning Phase")
    
            plan = self.executor.planning_phase(task, context)
    
    
    
            # === 阶段 5：ReAct 循环（带动态加载） ===
    
            cli.display_phase("Execution Phase")
    
    
    
            for step in range(self.max_steps):
    
                self.state.step_count = step + 1
    
    
    
                # 显示进度
    
                cli.display_progress(step + 1, self.max_steps, f"步骤 {step + 1}")
    
    
    
                # 每轮开始前重新加载上下文（动态）
    
                context = self.executor.load_context()
    
    
    
                # Think
    
                cli.display_thinking("分析当前状态...")
    
                think_result = self.executor.think_phase(task, context, self.state.observations)
    
    
    
                if think_result["action"] == "complete":
    
                    cli.display_result("任务完成", True)
    
                    logger.info("Task marked as complete")
    
                    break
    
    
    
                # Act
    
                action_result = self.executor.act_phase(think_result)
    
    
    
                # Observe
    
                observation = self.executor.observe_phase(think_result, action_result)
    
                self.state.observations.append(observation)
    
    
    
                # 定期反思（每 5 步）
    
                if (step + 1) % 5 == 0:
    
                    cli.display_thinking("反思执行结果...")
    
                    reflection = self.executor.reflection_phase()
    
                    if reflection.get("task_completed"):
    
                        cli.display_result("反思确认任务完成", True)
    
                        logger.info("Reflection indicates task complete")
    
    
    
                        # 提取决策和交付物
    
                        decisions = self.executor.extract_decisions(self.state.observations)
    
                        artifact_files = self.executor.extract_artifacts(self.state.observations)
    
    
    
                        # 触发阶段完成回填
    
                        if self.manifest:
    
                            current_stage = self.manifest_manager.get_current_stage()
    
                            if current_stage:
    
                                self._on_stage_complete(current_stage.id, decisions, artifact_files)
    
    
    
                        break
    
    
    
            # === 阶段 6：最终反思 ===
    
            cli.display_phase("Reflection Phase")
    
            final_reflection = self.executor.reflection_phase()
    
    
    
            # 显示完成信息
    
            cli.display_completion(f"执行完成 - 共 {self.state.step_count} 步")
    
            cli.display_footer()
    
    
    
            return {
    
                "status": "completed",
    
                "spec": self.spec.model_dump() if self.spec else {},
    
                "plan": plan.model_dump(),
    
                "steps_executed": self.state.step_count,
    
                "observations": len(self.state.observations),
    
                "reflection": final_reflection,
    
                "message": "Task execution completed"
    
            }