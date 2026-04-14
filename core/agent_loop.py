"""
NanoAgent - 主协调器
"""

from typing import Dict, Any
from loguru import logger
from infrastructure.config.manager import get_config_manager
from application.services.spec_initializer import SpecInitializer


class NanoAgent:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._load_all_configs(get_config_manager())
        self._initialize_components()
        logger.info("NanoAgent initialized")

    def _load_all_configs(self, config_manager) -> Dict[str, Any]:
        config = {}
        for module_name in ["core", "agent", "llm"]:
            config[module_name] = config_manager.get_module_config(module_name)
        return config

    def _initialize_components(self):
        from infrastructure.llm.client import NanoLLMClient
        from application.services.router import HybridRouter
        from application.services.manifest import ManifestManager
        from spec.context import ContextLoader
        from infrastructure.persistence.context import ContextManager
        from infrastructure.tools.registry import ToolRegistry
        from .agent_state import AgentState
        from .executor import AgentExecutor

        llm_config = self.config.get("llm", {}).get("default", {})
        model = llm_config.get("model", "openai/qwen3.5-plus")

        self.llm = NanoLLMClient(model=model)
        self.router = HybridRouter(self.llm)
        self.tools = ToolRegistry()
        self.manifest_manager = ManifestManager()
        self.context_loader = ContextLoader(self.manifest_manager)
        self.spec_initializer = SpecInitializer(llm_client=self.llm)
        self.state = AgentState()

        self.executor = AgentExecutor(
            llm_client=self.llm, router=self.router,
            manifest_manager=self.manifest_manager,
            context_loader=self.context_loader,
            tool_registry=self.tools, config=self.config, state=self.state,
        )

    def run(self, task: str) -> Dict[str, Any]:
        """主执行循环"""
        self.state.reset()
        logger.info(f"开始任务: {task[:100]}")

        from presentation.cli.interface import get_cli
        cli = get_cli()
        cli.display_header()

        # === 阶段1: 路由 ===
        cli.display_phase("任务分析")
        routing = self.executor.route_task(task)
        cli.display_result(f"任务类型: {routing.task_type}", True)

        # === 阶段2: Spec管理 ===
        if self.executor.should_init_spec(task, routing):
            self.manifest = self.executor.init_spec(task, routing, self.spec_initializer)
            if self.manifest:
                cli.display_phase("Spec 初始化")
                print(f"📋 项目: {self.manifest.project_name}, 阶段: {self.manifest.current_stage}")
        else:
            self.manifest = self.executor.load_existing_manifest()
            if self.manifest:
                cli.display_result(f"加载现有 Spec: {self.manifest.project_name}", True)

        # === 阶段3: 上下文加载 ===
        context = self.executor.load_context()
        self.state.add_message("system", self.executor.build_system_prompt(context))

        # === 阶段4: Planning ===
        cli.display_phase("Planning Phase")
        plan = self.executor.planning_phase(task, context)
        self.state.current_plan = plan

        # === 阶段5: ReAct主循环 ===
        return self._main_react_loop(task, plan, cli, context)

    def _main_react_loop(self, task, plan, cli, context) -> Dict[str, Any]:
        """简化的主ReAct循环 - 内层/外层结构"""
        max_steps = self.config.get("core", {}).get("performance", {}).get("max_steps", 20)
        reflection_interval = self.config.get("agent", {}).get("behavior", {}).get("reflection_interval", 5)

        cli.display_phase("Execution Phase")

        # 外层循环：用户交互和任务管理
        for step in range(max_steps):
            self.state.step_count = step + 1

            # 打印仪表盘 (每 3 步)
            if step % 3 == 0:
                try:
                    cli.print_dashboard(
                        stage_name=self.state.current_stage,
                        step_info=f"{step + 1}/{max_steps}",
                        artifacts=self.state.get_artifacts(),
                        last_action="Thinking..."
                    )
                except:
                    pass

            cli.display_progress(step + 1, max_steps, f"步骤 {step + 1}")
            context = self.executor.load_context()

            # 内层循环：LLM调用和工具执行链
            tool_chain_result = self._inner_llm_loop(task, context, cli, step)
            
            if tool_chain_result["should_break"]:
                return self._finalize(cli, plan, tool_chain_result["reason"])
            
            # 保存步骤上下文
            self._save_step_context(
                tool_chain_result["think_result"], 
                tool_chain_result["action_result"], 
                tool_chain_result["observation"]
            )

            # 定期反思
            if (step + 1) % reflection_interval == 0:
                cli.display_thinking("反思执行结果...")
                reflection = self.executor.reflection_phase(self.state.observations)

                if reflection.get("stage_completed"):
                    self._handle_stage_advance(cli)
                if reflection.get("task_completed"):
                    return self._finalize(cli, plan, "反思确认任务完成")

        return self._finalize(cli, plan, "达到最大步数")

    def _inner_llm_loop(self, task, context, cli, step) -> Dict[str, Any]:
        """
        内层LLM循环 - 处理工具调用链
        
        结构：
        - 调用LLM获取思考结果
        - 如果不需要工具，返回响应并跳出循环
        - 如果需要工具，执行它们，将结果添加到对话，继续循环
        - 持续循环直到LLM不再请求工具
        """
        max_tool_iterations = 5  # 防止无限循环
        
        for iteration in range(max_tool_iterations):
            # Think阶段
            think_result = self.executor.think_phase(
                task, context, self.state.observations, step,
            )
            action = think_result.get("action", "")
            
            # 检查是否需要终止
            if action == "complete":
                return {"should_break": True, "reason": "任务完成", "think_result": think_result}
            elif action == "wait":
                return {"should_break": True, "reason": "需要用户输入", "think_result": think_result}
            elif action == "stage_complete":
                self._handle_stage_advance(cli, think_result)
                return {"should_break": False, "reason": "阶段完成继续", "think_result": think_result}
            
            # Act阶段 - 执行工具
            if action == "tool_call" and think_result.get("tool"):
                cli.display_action("tool_call", f"{think_result.get('tool')} - {think_result.get('reason', '')}")
                action_result = self.executor.act_phase(think_result)
                
                # Observe: 记录执行结果
                observation = {"action": action, "result": str(action_result)[:500]}
                self.state.observations.append(observation)
                
                # 如果工具执行成功，继续循环以允许链式调用
                if isinstance(action_result, str) and not action_result.startswith("Error"):
                    cli.display_result(f"工具执行成功: {think_result.get('tool')}", success=True)
                    # 继续内层循环，让LLM决定下一步
                    continue
                else:
                    cli.display_error(f"工具执行失败: {action_result}")
                    # 工具失败，跳出内层循环
                    return {
                        "should_break": False,
                        "reason": "工具执行失败",
                        "think_result": think_result,
                        "action_result": action_result,
                        "observation": observation
                    }
            else:
                # 不需要工具调用，跳出内层循环
                return {
                    "should_break": False,
                    "reason": "无需工具调用",
                    "think_result": think_result,
                    "action_result": None,
                    "observation": None
                }
        
        # 达到最大工具迭代次数
        return {
            "should_break": False,
            "reason": "达到最大工具迭代次数",
            "think_result": think_result,
            "action_result": None,
            "observation": None
        }

    def _handle_stage_advance(self, cli, think_result=None):
        """处理阶段推进"""
        cli.display_result("阶段完成，正在推进到下一阶段...", True)
        decisions = think_result.get("decisions", []) if think_result else self.state.get_decisions()
        artifacts = think_result.get("artifacts", []) if think_result else self.state.get_artifacts()

        if not artifacts:
            artifacts = self.state.get_artifacts()

        try:
            current_stage = self.manifest_manager.get_current_stage()
            if current_stage:
                formatted_decisions = [
                    d if isinstance(d, dict) else {"decision": d, "rationale": "自动生成"}
                    for d in decisions
                ]
                self.manifest_manager.sync_and_backfill(
                    stage_id=current_stage.id, decisions=formatted_decisions,
                    completed_artifacts=artifacts, next_stage=True,
                )
                self.state.clear_decisions()
                self.state.clear_artifacts()
                self.executor.load_context()
                self.state.update_context("stage_advanced", True)

                new_stage = self.manifest_manager.get_current_stage()
                if new_stage:
                    cli.display_result(f"已推进到阶段: {new_stage.name}", True)
                else:
                    cli.display_result("所有阶段已完成！", True)
        except Exception as e:
            logger.error(f"Failed to advance stage: {e}")
            cli.display_result(f"阶段推进失败: {str(e)}", True)

    def _save_step_context(self, think_result, action_result, observation):
        """保存单步执行上下文"""
        new_decisions = []
        reason = think_result.get("reason", "")
        if reason and len(reason) > 20:
            new_decisions.append(reason[:200])

        new_artifacts = []
        if isinstance(action_result, str) and "Successfully wrote" in action_result:
            import re
            match = re.search(r"to (\S+)$", action_result)
            if match:
                new_artifacts.append(match.group(1))

        recent_obs = [str(observation)[:200]] if observation else []

        if new_decisions or new_artifacts or recent_obs:
            self.executor.save_context({
                "accumulated_decisions": new_decisions,
                "accumulated_artifacts": new_artifacts,
                "recent_observations": recent_obs,
            })
            for a in new_artifacts:
                self.state.add_artifact(a)
            for d in new_decisions:
                self.state.add_decision(d)

    def _finalize(self, cli, plan, reason: str) -> Dict[str, Any]:
        """完成执行"""
        cli.display_result(reason, True)
        decisions = self.state.get_decisions()
        artifacts = self.state.get_artifacts()

        self.executor.save_execution_result(decisions, artifacts)

        # 触发阶段完成回填
        if self.manifest and hasattr(self, "manifest_manager"):
            current_stage = self.manifest_manager.get_current_stage()
            if current_stage:
                stage_id = current_stage.id if hasattr(current_stage, "id") else current_stage.get("id", "unknown")
                self.manifest_manager.sync_and_backfill(
                    stage_id=stage_id,
                    decisions=[{"decision": d, "rationale": ""} for d in decisions] if decisions else [],
                    completed_artifacts=artifacts if artifacts else [],
                    next_stage=True,
                )

        # 最终反思
        cli.display_phase("Reflection Phase")
        final_reflection = self.executor.reflection_phase(self.state.observations)
        cli.display_completion(f"执行完成 - 共 {self.state.step_count} 步")
        cli.display_footer()

        return {
            "status": "completed",
            "plan": plan.model_dump() if hasattr(plan, "model_dump") else plan,
            "steps_executed": self.state.step_count,
            "observations": len(self.state.observations),
            "decisions": decisions,
            "artifacts": artifacts,
            "reflection": final_reflection,
            "message": f"Task execution completed: {reason}",
        }
