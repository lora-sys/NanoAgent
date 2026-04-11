"""
执行器 - NanoAgent
管理执行流程的各个阶段
"""

from typing import Dict, Any, Optional
from loguru import logger
from spec.models import AgentPlan
from core.interfaces import (
    ILLMClient,
    IRouter,
    IManifestManager,
    IContextLoader,
    ISpecGenerator,
)


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
        config: Dict[str, Any] = None,
        state: Any = None,
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
            state: Agent 状态管理器
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
        self.state = state  # 添加 state 引用

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
            confidence=f"{routing_decision.confidence:.2%}",
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
{context["master_spec"][:300]}

## 当前阶段约束
{context["current_stage_spec"]}

## 必须遵守的规则
{chr(10).join(f"- {c}" for c in always_constraints)}

## 禁止的操作
{chr(10).join(f"- {c}" for c in never_constraints)}
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
        logger.warning(
            f"Context truncated from {len(context)} to {len(truncated)} chars"
        )
        return truncated

    def _get_recent_observations_summary(
        self, observations: list, max_items: int = 5
    ) -> str:
        """获取最近的观察摘要"""
        if not observations:
            return "No observations yet"

        recent = observations[-max_items:]
        summary = []
        for i, obs in enumerate(recent, 1):
            obs_type = obs.get("type", "")

            if obs_type == "user_answer":
                # 用户回答：显示用户的回答内容
                user_answer = obs.get("user_answer", obs.get("raw", ""))
                summary.append(f"Step {i}: 用户回答了：{user_answer[:500]}")
            else:
                # 其他观察：显示标准摘要
                raw = obs.get("raw", "")
                summary.append(f"Step {i}: {raw[:150]}...")

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

        # 标准化constraints格式
        constraints = context.get("constraints")
        if constraints is None:
            constraints = {"always": [], "never": []}
        elif isinstance(constraints, list):
            # 如果是list，视为always约束
            constraints = {"always": constraints, "never": []}

        # 构建动态 Spec 内容（基于当前阶段）
        if context.get("master_spec") and context.get("current_stage_spec"):
            full_spec_content = f"""【当前任务阶段】

## 核心目标（来自 Master Spec）
{context["master_spec"][:300]}

## 当前阶段约束
{context["current_stage_spec"]}

## 必须遵守的规则
{chr(10).join(f"- {c}" for c in constraints.get("always", []))}

## 禁止的操作
{chr(10).join(f"- {c}" for c in constraints.get("never", []))}
"""
        else:
            # 回退到旧方式
            full_spec_content = "No spec context available"

        from core.prompt import SYSTEM_PROMPT, PLANNING_PROMPT
        from spec.models import AgentPlan, PlanStep
        import json

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": PLANNING_PROMPT.format(
                    task_description=task,
                    task_spec=full_spec_content,
                    current_context="",
                    available_tools=self.tool_registry.get_tool_descriptions()
                    if self.tool_registry
                    else "No tools available",
                ),
            },
        ]

        try:
            # 尝试使用结构化输出（更可靠）
            plan = self.llm_client.structured_chat(messages, AgentPlan, temperature=0.5)
            logger.info(f"Plan generated with {len(plan.steps)} steps")
            return plan

        except Exception as e:
            logger.warning(
                f"Structured planning failed, falling back to JSON parsing: {e}"
            )
            # 回退到 JSON 解析
            try:
                response = self.llm_client.chat(messages, temperature=0.5)
                plan_data = json.loads(response)
                plan = AgentPlan(
                    steps=[
                        PlanStep(
                            step_id=step["step_id"],
                            goal=step["goal"],
                            suggested_tools=step.get("tool", "").split(","),
                        )
                        for step in plan_data.get("steps", [])
                    ],
                    overall_goal=plan_data.get("overview", ""),
                )
                logger.info(f"Plan generated with {len(plan.steps)} steps (fallback)")
                return plan
            except Exception as e2:
                logger.error(f"Planning error: {e2}")
                # 生成简单计划作为回退
                return AgentPlan(
                    steps=[
                        PlanStep(step_id=1, goal="Execute task", suggested_tools=[])
                    ],
                    overall_goal="Fallback plan",
                )

    def think_phase(
        self,
        task: str,
        context: Dict,
        observations: list,
        step_count: int = 0,
        spec: Any = None,
    ) -> Dict:
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
        recent_observations = self._get_recent_observations_summary(
            observations, max_items=3
        )

        # 获取需求信息摘要
        requirements_summary = ""
        if hasattr(self, "state") and self.state:
            requirements_summary = self.state.get_requirements_summary()

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
            requirements=requirements_summary,
            available_tools=self.tool_registry.get_tool_descriptions()
            if self.tool_registry
            else "No tools available",
        )

        # 添加当前阶段约束
        if context.get("current_stage_spec"):
            prompt += "\n\n【当前阶段约束】\n"
            prompt += context["current_stage_spec"]

        if context.get("constraints"):
            constraints = context["constraints"]
            # 标准化constraints格式
            if isinstance(constraints, list):
                # 如果是list，转换为dict格式
                constraints = {"always": constraints, "never": []}
            elif not isinstance(constraints, dict):
                constraints = {}

            if constraints.get("never"):
                prompt += "\n【禁止操作】\n"
                for c in constraints["never"]:
                    prompt += f"- {c}\n"

        # 截断 prompt 以符合 token 限制
        prompt = self._truncate_context_for_tokens(prompt)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        response = self.llm_client.chat(messages, temperature=0.7)

        logger.debug(f"Think response: {response[:200]}...")

        # 添加重试机制来解析响应
        max_parse_retries = 3
        last_parse_error = None

        for parse_attempt in range(max_parse_retries):
            try:
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
                        logger.error(
                            f"Failed to parse STAGE_COMPLETE JSON: {e}", exc_info=True
                        )
                        logger.debug(
                            f"Response substring: {response[max(0, start - 50) : min(len(response), end + 50)] if start != -1 else response[:100]}"
                        )

                    return {
                        "action": "stage_complete",
                        "stage_id": context.get("current_stage_id", "unknown"),
                        "decisions": decisions,
                        "artifacts": artifacts,
                    }
                else:
                    # 解析工具调用
                    # 尝试解析 JSON 格式的工具调用
                    if "{" in response and "}" in response:
                        start = response.find("{")
                        end = response.rfind("}") + 1
                        action_data = json.loads(response[start:end])

                        # 验证必需字段
                        if "action" not in action_data:
                            raise ValueError("Missing 'action' field in JSON response")

                        # 验证 action 类型
                        valid_actions = [
                            "tool_call",
                            "complete",
                            "wait",
                            "stage_complete",
                            "continue",
                        ]
                        if action_data["action"] not in valid_actions:
                            raise ValueError(f"Invalid action: {action_data['action']}")

                        if action_data["action"] == "tool_call":
                            if (
                                "tool" not in action_data
                                and "function" not in action_data
                            ):
                                raise ValueError(
                                    "Missing 'tool' or 'function' field for tool_call action"
                                )

                            tool_name = action_data.get("tool") or action_data.get(
                                "function"
                            )
                            arguments = action_data.get(
                                "arguments", action_data.get("parameters", {})
                            )
                            return {
                                "action": "tool_call",
                                "tool": tool_name,
                                "arguments": arguments,
                                "thought": action_data.get("thought", ""),
                            }
                        else:
                            return action_data

                    # 回退：基于文本解析
                    return {
                        "action": "tool_call",
                        "tool": "unknown",
                        "arguments": {},
                        "thought": response[:200],
                    }

            except Exception as e:
                last_parse_error = e
                logger.warning(f"Parse attempt {parse_attempt + 1} failed: {e}")

                # 如果不是最后一次尝试，重新生成响应
                if parse_attempt < max_parse_retries - 1:
                    logger.info(
                        f"Retrying think phase... ({parse_attempt + 2}/{max_parse_retries})"
                    )
                    # 添加错误反馈到 prompt
                    messages.append(
                        {
                            "role": "user",
                            "content": f"上一次的响应解析失败: {str(e)}\n请重新生成一个格式正确的 JSON 响应。",
                        }
                    )
                    response = self.llm_client.chat(messages, temperature=0.7)
                    logger.debug(f"Retry response: {response[:200]}...")
                else:
                    logger.error(
                        f"Failed to parse think response after {max_parse_retries} attempts: {e}"
                    )

        # 所有解析尝试都失败，返回安全的默认值
        logger.error(
            f"All parse attempts failed, using fallback action. Last error: {last_parse_error}"
        )
        return {
            "action": "continue",
            "thought": "Parse failed, continuing with fallback",
            "parse_error": str(last_parse_error),
        }

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
                # HITL 工具会自动在get_tool时动态加载，无需手动加载
                pass

            # 增强的参数映射规则
            param_mappings = {
                "write_file": {
                    "filepath": ["path", "file_path", "filename", "file"],
                    "content": ["text", "data", "body"],
                    "mode": ["write_mode", "file_mode"],
                },
                "read_file": {
                    "filepath": ["path", "file_path", "filename", "file"],
                    "offset": ["start_line", "from_line"],
                    "limit": ["max_lines", "line_count"],
                },
                "list_directory": {
                    "path": ["directory", "dir", "folder"],
                    "ignore": ["ignore_patterns", "exclude", "skip"],
                },
                "safe_write_file": {
                    "filepath": ["path", "file_path", "filename", "file"],
                    "content": ["text", "data", "body"],
                    "mode": ["write_mode", "file_mode"],
                },
                "safe_read_file": {
                    "filepath": ["path", "file_path", "filename", "file"],
                    "offset": ["start_line", "from_line"],
                    "limit": ["max_lines", "line_count"],
                },
                "safe_list_directory": {
                    "path": ["directory", "dir", "folder"],
                    "ignore": ["ignore_patterns", "exclude", "skip"],
                },
            }

            # 应用参数映射
            if tool_name in param_mappings:
                mappings = param_mappings[tool_name]
                for target_param, source_params in mappings.items():
                    # 如果目标参数不存在，尝试从源参数映射
                    if target_param not in arguments:
                        for source_param in source_params:
                            if source_param in arguments:
                                arguments[target_param] = arguments.pop(source_param)
                                logger.info(
                                    f"Mapped '{source_param}' to '{target_param}' for {tool_name}"
                                )
                                break

            # 执行工具，带重试机制
            max_retries = 3
            result = None
            last_error = None

            for attempt in range(max_retries):
                try:
                    result = (
                        self.tool_registry.execute(tool_name, arguments)
                        if self.tool_registry
                        else f"Tool registry not available: {tool_name}"
                    )

                    # 如果执行成功，返回结果
                    if result:
                        if attempt > 0:
                            logger.info(
                                f"Tool execution succeeded after {attempt + 1} attempts"
                            )
                        return result

                except Exception as e:
                    last_error = e
                    logger.warning(f"Tool execution attempt {attempt + 1} failed: {e}")

                    # 如果不是最后一次尝试，等待一段时间后重试
                    if attempt < max_retries - 1:
                        import time

                        time.sleep(1 * (attempt + 1))  # 递增延迟
                    else:
                        logger.error(
                            f"Tool execution failed after {max_retries} attempts: {e}"
                        )
                        # 返回错误信息
                        return f"Error: Tool execution failed after {max_retries} attempts - {str(e)}"

            # 如果所有尝试都失败，返回最后一个错误
            if last_error:
                return f"Error: {str(last_error)}"
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

        # 截断工具结果以减少 token 使用（对于用户回答，限制1000字符）
        tool_result_str = str(result)[:1000]

        # 检查是否为 HITL 工具
        from core.tools.hitl import HITL_TOOL_NAMES

        is_hitl_tool = action.get("tool") in HITL_TOOL_NAMES

        if is_hitl_tool and tool_result_str:
            # HITL 工具：直接存储用户回答，不调用 LLM 分析
            logger.info(f"User answer captured: {tool_result_str[:100]}...")

            # 提取并保存需求信息
            self._extract_and_save_requirements(tool_result_str, action)

            # 提取并保存决策（从用户回答中）
            if hasattr(self, "state") and self.state:
                decision = self._extract_decision_from_answer(tool_result_str)
                if decision:
                    self.state.add_decision(
                        decision=decision,
                        rationale="用户确认",
                        step=self.state.step_count,
                    )

            return {
                "raw": tool_result_str,
                "summary": f"User answered: {tool_result_str[:200]}",
                "type": "user_answer",
                "user_answer": tool_result_str,
                "timestamp": self._get_timestamp(),
            }

        # 其他工具：调用 LLM 分析
        from core.prompt import SYSTEM_PROMPT, REACT_OBSERVE_PROMPT
        import json

        # 对非 HITL 工具的结果，截断到 500 字符
        tool_result_str_for_analysis = str(result)[:500]

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": REACT_OBSERVE_PROMPT.format(
                    last_action=json.dumps(action, indent=2),
                    tool_result=tool_result_str_for_analysis,
                ),
            },
        ]

        try:
            response = self.llm_client.chat(messages, temperature=0.7)

            # 提取并保存交付物（从文件写入操作中）
            if hasattr(self, "state") and self.state:
                artifact = self._extract_artifact_from_action(action, result)
                if artifact:
                    self.state.add_artifact(
                        artifact_path=artifact,
                        description=f"Created {artifact}",
                        step=self.state.step_count,
                    )

            return {
                "raw": response,
                "summary": response[:200] if len(response) > 200 else response,
                "type": "tool_observation",
            }

        except Exception as e:
            logger.error(f"Observe phase error: {e}")
            return {
                "raw": f"Error during observation: {str(e)}",
                "summary": "Observation failed",
                "type": "error",
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
        execution_summary = self._get_recent_observations_summary(
            observations, max_items=10
        )

        # 处理 spec 可能为 None 的情况
        task_spec_json = spec.model_dump_json(indent=2) if spec else "{}"

        # 获取当前阶段的成功标准
        stage_success_criteria = "暂无阶段成功标准"
        if (
            hasattr(self, "state")
            and self.state
            and hasattr(self.state, "current_context")
        ):
            context = self.state.current_context
            if context.get("current_stage_spec"):
                # 从当前阶段 spec 中提取成功标准
                stage_spec = context["current_stage_spec"]
                if "成功标准" in stage_spec or "Success Criteria" in stage_spec:
                    stage_success_criteria = stage_spec

        from core.prompt import SYSTEM_PROMPT, REFLECTION_PROMPT
        from pydantic import BaseModel, Field
        from typing import List
        import json

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": REFLECTION_PROMPT.format(
                    execution_history=execution_summary,
                    task_spec=task_spec_json,
                    current_progress=f"{len(observations)} steps completed",
                    stage_success_criteria=stage_success_criteria,
                ),
            },
        ]

        # 截断 prompt 以符合 token 限制
        user_content = messages[1]["content"]
        messages[1]["content"] = self._truncate_context_for_tokens(user_content)

        try:
            # 尝试使用结构化输出
            class ReflectionResult(BaseModel):
                task_completed: bool
                stage_completed: bool = False
                progress_summary: str
                issues_found: List[str] = Field(default_factory=list)
                solutions_applied: List[str] = Field(default_factory=list)
                next_action: str
                confidence_score: float = 0.5
                decisions: List[str] = Field(default_factory=list)
                artifacts: List[str] = Field(default_factory=list)

            reflection = self.llm_client.structured_chat(
                messages, ReflectionResult, temperature=0.5
            )
            logger.info(
                f"Reflection: {reflection.next_action}, stage_completed: {reflection.stage_completed}"
            )
            return reflection.model_dump()

        except Exception as e:
            logger.warning(
                f"Structured reflection failed, falling back to JSON parsing: {e}"
            )
            # 回退到 JSON 解析
            try:
                response = self.llm_client.chat(messages, temperature=0.5)
                reflection = json.loads(response)
                logger.info(f"Reflection: {reflection.get('next_action', 'unknown')}")
                return reflection
            except Exception as e:
                logger.warning(
                    f"Structured reflection failed, falling back to continue: {e}"
                )
                return {
                    "task_completed": False,
                    "stage_completed": False,
                    "next_action": "continue",
                }

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

    def init_spec(
        self, task: str, routing_decision: Dict, spec_initializer: Any = None
    ) -> Any:
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

        logger.info(
            f"Spec initialized: {manifest.project_name if manifest else 'Failed'}"
        )
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
                    "timestamp": self._get_timestamp(),
                }

                # 检查persistence_manager是否有save方法
                if hasattr(self.persistence_manager, "save"):
                    self.persistence_manager.save(result)
                elif hasattr(self.persistence_manager, "persist"):
                    self.persistence_manager.persist(result)
                else:
                    logger.warning("PersistenceManager has no save/persist method")

                logger.info(
                    f"Saved execution result: {len(decisions)} decisions, {len(artifacts)} artifacts"
                )
            except Exception as e:
                logger.error(f"Failed to save execution result: {e}")

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime

        return datetime.now().isoformat()

    def _extract_and_save_requirements(self, user_answer: str, action: Dict):
        """
        从用户回答中提取并保存需求信息

        Args:
            user_answer: 用户回答内容
            action: 执行的动作
        """
        # 如果没有 state 对象，跳过
        if not hasattr(self, "state") or not self.state:
            return

        # 检查是否是确认回答
        confirmation_keywords = ["ok", "好的", "是的", "确认", "没问题", "可以", "行"]
        user_answer_lower = user_answer.lower()

        # 如果用户回答是确认，标记需求已确认
        if any(keyword in user_answer_lower for keyword in confirmation_keywords):
            self.state.confirm_requirements()
            logger.info("User confirmed requirements")
            return

        # 提取关键需求信息
        # 1. 提取核心模块
        module_keywords = ["模块", "板块", "章节", "部分", "功能"]
        for keyword in module_keywords:
            if keyword in user_answer:
                self.state.save_requirement(
                    "core_modules", user_answer, category="modules"
                )
                break

        # 2. 提取视觉风格
        style_keywords = ["颜色", "色调", "风格", "视觉", "设计", "色系"]
        for keyword in style_keywords:
            if keyword in user_answer:
                self.state.save_requirement(
                    "visual_style", user_answer, category="style"
                )
                break

        # 3. 提取技术范围
        tech_keywords = ["技术", "交互", "动画", "静态", "动态", "功能"]
        for keyword in tech_keywords:
            if keyword in user_answer:
                self.state.save_requirement(
                    "tech_scope", user_answer, category="tech_scope"
                )
                break

        # 4. 提取展示方式
        display_keywords = ["展示", "链接", "在线", "本地", "演示"]
        for keyword in display_keywords:
            if keyword in user_answer:
                self.state.save_requirement(
                    "display_method", user_answer, category="display"
                )
                break

        # 5. 提取内容准备情况
        content_keywords = ["文案", "内容", "文字", "准备"]
        for keyword in content_keywords:
            if keyword in user_answer:
                self.state.save_requirement(
                    "content_preparation", user_answer, category="content"
                )
                break

        # 6. 提取参考资源
        reference_keywords = ["参考", "借鉴", "类似", "样例", "设计稿"]
        for keyword in reference_keywords:
            if keyword in user_answer:
                self.state.save_requirement(
                    "references", user_answer, category="references"
                )
                break

        # 保存完整的用户回答
        self.state.save_requirement(
            f"user_answer_{self.state.step_count}", user_answer, category="user_answers"
        )

    def _extract_artifact_from_action(self, action: Dict, result: Any) -> Optional[str]:
        """
        从工具调用中提取交付物路径

        Args:
            action: 执行的动作
            result: 执行结果

        Returns:
            交付物路径，如果没有则返回 None
        """
        tool_name = action.get("tool", "")
        arguments = action.get("arguments", {})

        # 检查是否为文件写入操作
        if tool_name in ["write_file", "safe_write_file"]:
            filepath = (
                arguments.get("filepath")
                or arguments.get("path")
                or arguments.get("file_path")
            )
            if filepath and "Successfully wrote" in str(result):
                return filepath

        return None

    def _extract_decision_from_answer(self, user_answer: str) -> Optional[str]:
        """
        从用户回答中提取决策

        Args:
            user_answer: 用户回答

        Returns:
            决策内容，如果没有则返回 None
        """
        # 检查是否为确认回答
        confirmation_keywords = [
            "ok",
            "好的",
            "是的",
            "确认",
            "没问题",
            "可以",
            "行",
            "同意",
        ]
        user_answer_lower = user_answer.lower()

        if any(keyword in user_answer_lower for keyword in confirmation_keywords):
            # 如果是确认，返回一个通用的确认决策
            return "用户确认需求"

        # 检查是否包含决策关键词
        decision_keywords = ["决定", "选择", "采用", "使用", "需要", "要"]
        for keyword in decision_keywords:
            if keyword in user_answer:
                # 提取包含关键词的句子
                sentences = user_answer.split("，|。|；|！")
                for sentence in sentences:
                    if keyword in sentence:
                        return sentence.strip()[:100]

        return None
