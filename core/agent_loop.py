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
    
    def __init__(self, model: str = "openai/qwen3.5-plus", max_steps: int = 20, max_context_tokens: int = 3500):
        self.llm = NanoLLMClient(model)
        self.max_steps = max_steps
        self.max_context_tokens = max_context_tokens  # 最大上下文 token 限制（留有余量）
        self.state = AgentState()
        self.tools = ToolRegistry()
        self.spec: Optional[TaskSpec] = None
        
        # 新增：路由器和 Spec 管理器
        self.router = HybridRouter(self.llm)
        self.spec_initializer = SpecInitializer()
        self.manifest_manager = ManifestManager()
        self.manifest = None
        self.current_stage_context = {}
        
        # 预加载文件工具（常用工具）
        self._preload_file_tools()
        
        logger.add("nanoagent.log", rotation="10 MB")
        logger.info("NanoAgent initialized with Spec-Driven and Dynamic Tool Loading")
    
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
    
    def _dynamic_load_context(self) -> Dict:
        """动态加载当前阶段的上下文（核心方法）"""
        context = {
            "master_spec": "",
            "current_stage_spec": "",
            "constraints": []
        }
        
        try:
            # 1. 加载 manifest
            manifest = self.manifest_manager.load_manifest()
            if not manifest:
                logger.warning("No manifest found, skipping dynamic load")
                return context
            
            # 2. 加载 master_spec（保持方向）
            master_spec = self.manifest_manager.load_master_spec()
            if master_spec:
                context["master_spec"] = master_spec
                logger.info("✓ Loaded master_spec for direction alignment")
            
            # 3. 加载当前阶段 spec（确保细节）
            current_stage_spec = self.manifest_manager.load_current_stage_spec()
            if current_stage_spec:
                context["current_stage_spec"] = current_stage_spec
                logger.info(f"✓ Loaded current stage spec: {manifest.current_stage}")
            
            # 4. 提取约束
            if master_spec:
                constraints = self._extract_constraints(master_spec)
                context["constraints"] = constraints
            
            self.current_stage_context = context
            return context
            
        except Exception as e:
            logger.error(f"Dynamic load failed: {e}")
            return context
    
    def _extract_constraints(self, spec_content: str) -> Dict:
        """从 Spec 内容中提取约束"""
        constraints = {
            "always": [],
            "ask_first": [],
            "never": []
        }
        
        lines = spec_content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if "**必须做" in line or "Always" in line:
                current_section = "always"
            elif "**先询问" in line or "Ask First" in line:
                current_section = "ask_first"
            elif "**绝对禁止" in line or "Never" in line:
                current_section = "never"
            elif line.startswith("-") and current_section:
                constraint = line[1:].strip()
                if constraint:
                    constraints[current_section].append(constraint)
        
        return constraints
    
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
        success = self.manifest_manager.sync_and_backfill(
            stage_id=stage_id,
            decisions=decisions,
            completed_artifacts=artifacts,
            next_stage=True
        )
        
        if success:
            # 显示进度条
            progress = self.manifest_manager.get_progress_bar()
            print(f"📊 进度: {progress}\n")
            
            # 显示下一阶段
            next_stage = self.manifest_manager.get_current_stage()
            if next_stage:
                print(f"➡️  下一阶段: {next_stage}\n")
        else:
            logger.error("Stage complete failed")
    
    def _generate_spec(self, task: str) -> TaskSpec:
        """根据用户任务生成高质量 Spec（使用模板系统）"""
        from identity.soul_loader import load_soul
        from identity.template_loader import load_template, fill_template
        from pydantic import BaseModel, Field
        from typing import List

        # 创建临时模型来接收 LLM 响应
        class SpecContent(BaseModel):
            task_type: str
            overall_goal: str
            success_criteria: List[str] = Field(default_factory=list)
            current_progress: str = ""
            completed_steps: List[str] = Field(default_factory=list)
            remaining: List[str] = Field(default_factory=list)
            always: List[str] = Field(default_factory=list)
            ask_first: List[str] = Field(default_factory=list)
            never: List[str] = Field(default_factory=list)
            self_check_instructions: List[str] = Field(default_factory=list)
            process_requirements: List[str] = Field(default_factory=list)

        # 步骤 1: 用 LLM 生成 task_type 和核心字段值
        soul_content = load_soul()

        prompt = f"""你是一个专业的 Spec 内容生成器。

Agent 灵魂描述：
{soul_content}

当前用户任务：
{task}

请生成一个完整的 Spec 内容 JSON 对象。

JSON Schema:
{{
  "task_type": "string (chat/code/writing/analyze)",
  "overall_goal": "string - 核心目标",
  "success_criteria": ["string1", "string2", ...],
  "current_progress": "string",
  "completed_steps": ["step1", "step2", ...],
  "remaining": ["step3", "task4", ...],
  "always": ["action1", "action2", ...],
  "ask_first": ["action1", "action2", ...],
  "never": ["action1", "action2", ...],
  "self_check_instructions": ["instruction1", "instruction2", ...],
  "process_requirements": ["string1", "string2", ...]
}}

要求：
- success_criteria 必须具体、可验证
- current_progress 描述当前阶段
- completed_steps 和 remaining 是步骤列表
- always/ask_first/never 是行为规则列表
- 严格遵守 Three-Tier Boundaries

重要：只返回合法的 JSON，不要任何额外文字。"""

        messages = [
            {"role": "system", "content": "你是一个严谨的 Spec 内容生成器，只输出 JSON。"},
            {"role": "user", "content": prompt}
        ]

        spec_content: SpecContent = self.llm.structured_chat(messages, SpecContent, temperature=0.3)

        # 步骤 2: 根据 task_type 加载对应的模板
        template = load_template(spec_content.task_type)
        if template is None:
            logger.warning(f"Template not found for task_type: {spec_content.task_type}, using base template")
            template = load_template("base")
            if template is None:
                logger.warning("No template available, creating spec directly from content")
                # 如果没有模板，直接从内容创建 TaskSpec
                return TaskSpec(
                    task_type=spec_content.task_type,
                    overall_goal=spec_content.overall_goal,
                    success_criteria=spec_content.success_criteria,
                    progress_tracking={
                        "current_progress": spec_content.current_progress,
                        "completed_steps": spec_content.completed_steps,
                        "remaining": spec_content.remaining
                    },
                    process_requirements=spec_content.process_requirements,
                    boundaries={
                        "always": spec_content.always,
                        "ask_first": spec_content.ask_first,
                        "never": spec_content.never
                    },
                    self_check_instructions=spec_content.self_check_instructions,
                    human_in_loop_points=[],
                    additional_notes=""
                )

        # 步骤 3: 用 LLM 生成的值填充模板占位符
        filled_template = fill_template(
            template,
            overall_goal=spec_content.overall_goal,
            task_type=spec_content.task_type,
            success_criteria="\n".join(f"- {c}" for c in spec_content.success_criteria),
            current_progress=spec_content.current_progress,
            completed_steps="\n".join(f"- {s}" for s in spec_content.completed_steps),
            remaining_steps="\n".join(f"- {s}" for s in spec_content.remaining),
            always="\n".join(f"- {a}" for a in spec_content.always),
            ask_first="\n".join(f"- {a}" for a in spec_content.ask_first),
            never="\n".join(f"- {n}" for n in spec_content.never),
            self_check_instructions="\n".join(f"- {i}" for i in spec_content.self_check_instructions)
        )

        # 步骤 4: 将填充后的模板内容转换为 TaskSpec 对象
        spec = TaskSpec(
            task_type=spec_content.task_type,
            overall_goal=spec_content.overall_goal,
            success_criteria=spec_content.success_criteria,
            progress_tracking={
                "current_progress": spec_content.current_progress,
                "completed_steps": spec_content.completed_steps,
                "remaining": spec_content.remaining
            },
            process_requirements=spec_content.process_requirements,
            boundaries={
                "always": spec_content.always,
                "ask_first": spec_content.ask_first,
                "never": spec_content.never
            },
            self_check_instructions=spec_content.self_check_instructions,
            human_in_loop_points=[],
            additional_notes=filled_template  # 将填充后的模板保存在 additional_notes 中
        )

        logger.info(
            "Spec generated with template",
            task_type=spec.task_type,
            goal=spec.overall_goal,
            template_used=template is not None
        )
        return spec
    
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
            except:
                pass
            
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
            hitl_tools = ["present_decision_for_approval", "escalate_to_human", "collect_human_feedback", 
                          "monitor_agent", "human_intervention", "ask_user_question"]
            
            if tool_name in hitl_tools:
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
        self.state.observations.append({
            "step": self.state.step_count,
            "action": action,
            "result": tool_result_str,
            "analysis": response[:200]
        })
        
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
            except:
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
    
            routing_decision = self.router.route(task)
    
            cli.display_result(f"任务类型: {routing_decision.task_type.value}", True)
    
            cli.display_result(f"置信度: {routing_decision.confidence:.2%}", True)
    
            
    
            # === 阶段 2：Spec 初始化（如果需要） ===
    
            if self._should_init_spec(task, routing_decision):
    
                cli.display_phase("Spec 初始化")
    
                self.manifest = self.spec_initializer.init_spec(task, routing_decision)
    
                
    
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
    
            context = self._dynamic_load_context()
    
            
    
            # 构建系统提示（只包含当前阶段的约束）
    
            system_prompt = self._build_stage_system_prompt(context)
    
            self.state.add_message("system", system_prompt)
    
            
    
            # === 阶段 4：Planning 阶段 ===
    
            cli.display_phase("Planning Phase")
    
            plan = self._planning_phase(task, context)
    
            
    
            # === 阶段 5：ReAct 循环（带动态加载） ===
    
            cli.display_phase("Execution Phase")
    
            
    
            for step in range(self.max_steps):
    
                self.state.step_count = step + 1
    
                
    
                # 显示进度
    
                cli.display_progress(step + 1, self.max_steps, f"步骤 {step + 1}")
    
                
    
                # 每轮开始前重新加载上下文（动态）
    
                context = self._dynamic_load_context()
    
                
    
                # Think
    
                cli.display_thinking("分析当前状态...")
    
                think_result = self._react_think(task, context)
    
                
    
                if think_result["action"] == "complete":
    
                    cli.display_result("任务完成", True)
    
                    logger.info("Task marked as complete")
    
                    break
    
                elif think_result["action"] == "stage_complete":
    
                    # 阶段完成，执行回填
    
                    cli.display_result(f"阶段完成: {think_result.get('stage_id')}", True)
    
                    self._on_stage_complete(
    
                        think_result.get("stage_id"),
    
                        think_result.get("decisions", []),
    
                        think_result.get("artifacts", [])
    
                    )
    
                    continue
    
                
    
                # Act
    
                action_result = self._react_act(think_result)
    
                
    
                # Observe
    
                observation = self._react_observe(think_result, action_result)
    
                
    
                # 定期反思（每 5 步）
    
                if (step + 1) % 5 == 0:
    
                    cli.display_thinking("反思执行结果...")
    
                    reflection = self._reflection_phase()
    
                    if reflection.get("task_completed"):
    
                        cli.display_result("反思确认任务完成", True)
    
                        logger.info("Reflection indicates task complete")
    
                        
    
                        # 提取决策和交付物
    
                        decisions = self._extract_decisions()
    
                        artifacts = [obs.get("raw", "") for obs in self.state.observations 
    
                                  if "Successfully wrote" in obs.get("raw", "")]
    
                        
    
                        # 提取文件名
    
                        import re
    
                        artifact_files = []
    
                        for obs in self.state.observations:
    
                            match = re.search(r'Successfully wrote \d+ chars to (\S+)', obs.get("raw", ""))
    
                            if match:
    
                                artifact_files.append(match.group(1))
    
                        
    
                        # 触发阶段完成回填
    
                        if self.manifest:
    
                            current_stage = self.manifest.get_current_stage()
    
                            if current_stage:
    
                                self._on_stage_complete(current_stage, decisions, artifact_files)
    
                        
    
                        break
    
            
    
            # === 阶段 6：最终反思 ===
    
            cli.display_phase("Reflection Phase")
    
            final_reflection = self._reflection_phase()
    
            
    
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