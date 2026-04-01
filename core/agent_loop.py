from loguru import logger
from typing import Dict, List, Any, Optional
import json
from .llm_client import NanoLLMClient
from .tools import safe_read_file, safe_write_file
from .agent_state import AgentState, AgentPlan, PlanStep
from .prompt import (
    SYSTEM_PROMPT, PLANNING_PROMPT, REACT_THINK_PROMPT, 
    REACT_OBSERVE_PROMPT, REFLECTION_PROMPT, SELF_CHECK_PROMPT,
    ERROR_RECOVERY_PROMPT, HUMAN_REQUEST_PROMPT
)
from spec.base import TaskSpec

class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
    
    def register(self, name: str, func: callable, description: str, schema: Dict):
        """注册工具"""
        self.tools[name] = {
            "function": func,
            "description": description,
            "schema": schema
        }
        logger.info(f"Registered tool: {name}")
    
    def execute(self, name: str, arguments: Dict) -> Any:
        """执行工具"""
        if name not in self.tools:
            raise ValueError(f"Tool not found: {name}")
        
        tool = self.tools[name]
        try:
            result = tool["function"](**arguments)
            logger.info(f"Executed tool {name}: {result[:100] if isinstance(result, str) else 'OK'}")
            return result
        except Exception as e:
            logger.error(f"Tool execution error {name}: {e}")
            return f"Error: {str(e)}"
    
    def get_tool_schemas(self) -> List[Dict]:
        """获取工具的 OpenAI 格式 schema"""
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["schema"]
                }
            }
            for name, tool in self.tools.items()
        ]
    
    def get_tool_descriptions(self) -> str:
        """获取工具描述文本（包含参数说明）"""
        descriptions = []
        
        for name, tool in self.tools.items():
            desc = f"- {name}: {tool['description']}"
            
            # 添加参数说明
            schema = tool.get('schema', {})
            if 'properties' in schema:
                params = schema['properties']
                param_list = []
                
                for param_name, param_info in params.items():
                    param_desc = param_info.get('description', '')
                    required = param_name in schema.get('required', [])
                    required_mark = " [required]" if required else " [optional]"
                    param_list.append(f"  - {param_name}{required_mark}: {param_desc}")
                
                if param_list:
                    desc += "\n  参数:\n" + "\n".join(param_list)
            
            descriptions.append(desc)
        
        return "\n".join(descriptions)

class NanoAgent:
    """基于 Planning + ReAct 范式的 AI Agent"""
    
    def __init__(self, model: str = "openai/qwen3.5-plus", max_steps: int = 20, max_context_tokens: int = 3500):
        self.llm = NanoLLMClient(model)
        self.max_steps = max_steps
        self.max_context_tokens = max_context_tokens  # 最大上下文 token 限制（留有余量）
        self.state = AgentState()
        self.tools = ToolRegistry()
        self.spec: Optional[TaskSpec] = None
        
        # 注册基础工具
        self._register_default_tools()
        
        logger.add("nanoagent.log", rotation="10 MB")
        logger.info("NanoAgent initialized")
    
    def _register_default_tools(self):
        """注册默认工具"""
        from .tools import ReadFileInput, WriteFileInput
        
        self.tools.register(
            "read_file",
            safe_read_file,
            "读取文件内容（限制在 agent_workspace 目录）",
            ReadFileInput.model_json_schema()
        )
        
        self.tools.register(
            "write_file",
            safe_write_file,
            "写入文件内容（限制在 agent_workspace 目录）",
            WriteFileInput.model_json_schema()
        )
    
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
    
    def _planning_phase(self, task: str) -> AgentPlan:
        """规划阶段：生成执行计划"""
        logger.info("=== Planning Phase ===")
        
        # 首先尝试用结构化输出
        # 构建完整的 Spec 内容（包括模板）
        full_spec_content = f"""【TaskSpec - {self.spec.task_type}】

## 核心目标
{self.spec.overall_goal}

## 成功标准
{chr(10).join(f'- {c}' for c in self.spec.success_criteria)}

## 进度跟踪
- 当前进度: {self.spec.progress_tracking.get('current_progress', '')}
- 已完成步骤: {', '.join(self.spec.progress_tracking.get('completed_steps', []))}
- 剩余步骤: {', '.join(self.spec.progress_tracking.get('remaining', []))}

## 边界约束
**必须做 (Always):**
{chr(10).join(f'- {a}' for a in self.spec.boundaries.get('always', []))}

**先询问 (Ask First):**
{chr(10).join(f'- {a}' for a in self.spec.boundaries.get('ask_first', []))}

**绝对禁止 (Never):**
{chr(10).join(f'- {n}' for n in self.spec.boundaries.get('never', []))}

## 自检指令
{chr(10).join(f'- {i}' for i in self.spec.self_check_instructions)}

## 过程要求
{chr(10).join(f'- {r}' for r in self.spec.process_requirements)}

---

**JSON 格式:**
{self.spec.model_dump_json(indent=2)}"""

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
    
    def _react_think(self, task: str) -> Dict:
        """ReAct 循环 - Think 阶段"""
        logger.info(f"=== Think Phase (Step {self.state.step_count + 1}) ===")
        
        # 使用摘要而不是完整的观察记录
        recent_observations = self._get_recent_observations_summary(max_items=3)
        
        prompt = REACT_THINK_PROMPT.format(
            current_step=self.state.step_count + 1,
            completed_steps=[s.get("step", 0) for s in self.state.observations],
            step_count=self.state.step_count,
            max_steps=self.max_steps,
            task_goal=self.spec.overall_goal,
            recent_observations=recent_observations,
            available_tools=self.tools.get_tool_descriptions()
        )
        
        # 截断 prompt 以符合 token 限制
        prompt = self._truncate_context_for_tokens(prompt)
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages, temperature=0.7)
        
        # 在终端显示完整的 think response（便于调试）
        print(f"\n{'='*60}\n💭 Think Phase (Step {self.state.step_count + 1}):\n{'='*60}")
        print(response)
        print(f"{'='*60}\n")
        
        logger.debug(f"Think response: {response[:200]}...")
        
        # 解析决策
        if "TASK_COMPLETE" in response:
            return {"action": "complete", "reason": "Task completed"}
        elif "WAIT_FOR_USER" in response:
            return {"action": "wait", "reason": "Needs user input"}
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
        """ReAct 循环 - Act 阶段"""
        if action["action"] == "tool_call":
            logger.info(f"Executing tool: {action['tool']}")
            
            # 参数映射：处理常见的参数名差异
            tool_name = action["tool"]
            arguments = action.get("arguments", {}).copy()
            
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
            return result
        else:
            return action.get("content", "No action taken")
    
    def _react_observe(self, action: Dict, result: Any) -> Dict:
        """ReAct 循环 - Observe 阶段"""
        logger.info("=== Observe Phase ===")
        
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
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": REFLECTION_PROMPT.format(
                execution_history=execution_summary,
                task_spec=self.spec.model_dump_json(indent=2),
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
        """执行完整的 Planning + ReAct 循环"""
        logger.info("=== Starting new task ===", task=task[:100])
        
        # Step 1: 生成 Spec
        self.spec = self._generate_spec(task)
        
        # Step 2: 展示 Spec 给用户
        print(f"\n{'='*60}")
        print(f"📋 Generated Spec (Task Type: {self.spec.task_type})")
        print(f"{'='*60}\n")
        
        # 展示填充后的模板内容（如果存在）
        if self.spec.additional_notes:
            print(self.spec.additional_notes)
            print()
        
        # 展示 JSON 格式的 Spec
        print("--- JSON Format ---")
        print(self.spec.model_dump_json(indent=2))
        print(f"{'='*60}\n")
        
        # Step 3: 尝试保存 Spec（可选，如果权限允许）
        try:
            spec_json = self.spec.model_dump_json(indent=2)
            spec_filename = f"{self.spec.task_type}_spec.md"
            # 保存到当前目录，不需要 agent_workspace 前缀
            with open(spec_filename, 'w', encoding='utf-8') as f:
                f.write(f"# Generated Spec\n\n{self.spec.additional_notes}\n\n--- JSON Format ---\n\n{spec_json}")
            logger.info(f"Spec saved to: {spec_filename}")
        except Exception as e:
            logger.warning(f"Could not save spec file: {e}")
            logger.info("Continuing without saving spec file...")
        
        # Step 4: 注入执行上下文（包含完整的 Spec，包括模板内容）
        spec_content = f"""【TaskSpec - {self.spec.task_type}】

## 核心目标
{self.spec.overall_goal}

## 成功标准
{chr(10).join(f'- {c}' for c in self.spec.success_criteria)}

## 进度跟踪
- 当前进度: {self.spec.progress_tracking.get('current_progress', '')}
- 已完成步骤: {', '.join(self.spec.progress_tracking.get('completed_steps', []))}
- 剩余步骤: {', '.join(self.spec.progress_tracking.get('remaining', []))}

## 边界约束
**必须做 (Always):**
{chr(10).join(f'- {a}' for a in self.spec.boundaries.get('always', []))}

**先询问 (Ask First):**
{chr(10).join(f'- {a}' for a in self.spec.boundaries.get('ask_first', []))}

**绝对禁止 (Never):**
{chr(10).join(f'- {n}' for n in self.spec.boundaries.get('never', []))}

## 自检指令
{chr(10).join(f'- {i}' for i in self.spec.self_check_instructions)}

## 过程要求
{chr(10).join(f'- {r}' for r in self.spec.process_requirements)}

---

**请严格按照以上 Spec 执行任务。**"""

        self.state.add_message("system", spec_content)
        
        # Step 4: Planning 阶段
        plan = self._planning_phase(task)
        
        # Step 5: ReAct 循环
        for step in range(self.max_steps):
            self.state.step_count = step + 1
            
            # Think
            think_result = self._react_think(task)
            
            if think_result["action"] == "complete":
                logger.info("Task marked as complete")
                break
            elif think_result["action"] == "wait":
                logger.info("Waiting for user input")
                break
            
            # Act
            action_result = self._react_act(think_result)
            
            # Observe
            observation = self._react_observe(think_result, action_result)
            
            # 定期反思（每 5 步）
            if (step + 1) % 5 == 0:
                reflection = self._reflection_phase()
                if reflection.get("task_completed"):
                    logger.info("Reflection indicates task complete")
                    break
        
        # Step 6: 最终反思
        final_reflection = self._reflection_phase()
        
        return {
            "status": "completed",
            "spec": self.spec.model_dump(),
            "plan": plan.model_dump(),
            "steps_executed": self.state.step_count,
            "observations": len(self.state.observations),
            "reflection": final_reflection,
            "message": "Task execution completed"
        }