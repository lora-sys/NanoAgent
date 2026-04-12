"""
NanoAgent - 主协调器（简化版）
纯粹的协调逻辑，所有业务逻辑委托给专门的模块
"""

from typing import Dict, Any
from loguru import logger
from infrastructure.config.manager import get_config_manager, ConfigManager
from core.agent_state import AgentState
from .executor import AgentExecutor
from infrastructure.container import DIContainer
from application.services.spec_initializer import SpecInitializer


class NanoAgent:
    """NanoAgent - 主协调器（简化版，纯粹的协调逻辑）"""

    def __init__(self, config: Dict[str, Any] = None, container: DIContainer = None):
        """
        初始化协调器

        Args:
            config: 配置字典（优先级最高）
            container: 依赖注入容器
        """
        # 配置管理
        if config:
            self.config = config
        elif container and container.has(ConfigManager):
            config_manager = container.get(ConfigManager)
            self.config = self._load_all_configs(config_manager)
        else:
            config_manager = get_config_manager()
            self.config = self._load_all_configs(config_manager)

        # 通过依赖注入获取各个组件
        if container:
            self.executor = container.get(AgentExecutor)
            self.state = container.get(AgentState)
            self.spec_initializer = (
                container.get(SpecInitializer)
                if container.has(SpecInitializer)
                else SpecInitializer(
                    llm_client=self.executor.llm_client
                )  # 从 executor 获取 llm_client
            )
            # 从 executor 中获取 manifest_manager（因为 executor 已经有这个引用）
            self.manifest_manager = self.executor.manifest_manager
        else:
            # 向后兼容的传统初始化
            self._initialize_components()

        logger.info("NanoAgent initialized as coordinator")

    def run(self, task: str) -> Dict[str, Any]:
        """
        主执行循环 - 纯粹的协调逻辑

        Args:
            task: 用户任务

        Returns:
            执行结果
        """
        # 重置状态，避免重用之前的数据
        self.state.reset()

        # 记录任务开始
        logger.info(f"开始任务: {task[:100]}")

        # 初始化CLI
        from cli_interface import get_cli

        cli = get_cli()
        cli.display_header()
        logger.info("=== Starting new task ===", task=task[:100])

        # === 阶段1: 路由 ===
        cli.display_phase("任务分析")
        logger.info("开始任务路由分析")
        routing_decision = self.executor.route_task(task)
        logger.info(
            f"路由结果: {routing_decision.task_type}, "
            f"置信度: {routing_decision.confidence:.2%}"
        )
        cli.display_result(f"任务类型: {routing_decision.task_type}", True)
        cli.display_result(f"置信度: {routing_decision.confidence:.2%}", True)

        # === 阶段2: Spec管理 ===
        if self.executor.should_init_spec(task, routing_decision):
            logger.info("开始Spec初始化")
            self.manifest = self.executor.init_spec(
                task, routing_decision, self.spec_initializer
            )
            if self.manifest:
                logger.info(
                    f"Spec初始化完成: {self.manifest.project_name}, "
                    f"阶段: {self.manifest.current_stage}"
                )
                cli.display_phase("Spec 初始化")
                print("\n📋 Spec 概要")
                print(f"{'=' * 60}")
                print(f"项目名称: {self.manifest.project_name}")
                print(f"当前阶段: {self.manifest.current_stage}")
                print(f"总阶段数: {len(self.manifest.pipeline)}")
                print(f"{'=' * 60}\n")
        else:
            self.manifest = self.executor.load_existing_manifest()
            if self.manifest:
                cli.display_result(f"加载现有 Spec: {self.manifest.project_name}", True)

        # === 阶段3: 上下文加载 ===
        context = self.executor.load_context()
        system_prompt = self.executor.build_system_prompt(context)
        self.state.add_message("system", system_prompt)

        # === 阶段4: Planning ===
        cli.display_phase("Planning Phase")
        plan = self.executor.planning_phase(task, context)

        # 保存plan到state
        self.state.current_plan = plan

        # === 阶段5: ReAct主循环 ===
        return self._main_react_loop(task, plan, cli, context)

    def _main_react_loop(
        self, task: str, plan, cli, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """主ReAct循环"""
        max_steps = (
            self.config.get("core", {}).get("performance", {}).get("max_steps", 20)
        )
        reflection_interval = (
            self.config.get("agent", {})
            .get("behavior", {})
            .get("reflection_interval", 5)
        )

        cli.display_phase("Execution Phase")

        for step in range(max_steps):
            self.state.step_count = step + 1
            cli.display_progress(step + 1, max_steps, f"步骤 {step + 1}")

            # 重新加载上下文
            context = self.executor.load_context()

            # Think -> Act -> Observe
            think_result = self.executor.think_phase(
                task, context, self.state.observations, step
            )

            # 处理不同的动作类型
            action = think_result.get("action", "")

            if action == "complete":
                return self._finalize_execution(cli, plan, "任务完成")
            elif action == "wait":
                # 等待用户输入
                cli.display_result("等待用户输入...", True)
                return self._finalize_execution(cli, plan, "需要用户输入")
            elif action == "stage_complete":
                # 阶段完成
                cli.display_result("阶段完成", True)
                # 提取决策和交付物
                decisions = think_result.get("decisions", [])
                artifacts = think_result.get("artifacts", [])

                # 如果 think_result 中没有 artifacts，尝试从 AgentState 中提取
                if not artifacts:
                    artifacts = self.state.get_artifacts()
                    logger.info(f"Extracted {len(artifacts)} artifacts from AgentState")

                # 推进到下一阶段
                try:
                    current_stage = self.manifest_manager.get_current_stage()
                    if current_stage:
                        # 转换 decisions 格式
                        formatted_decisions = []
                        for d in decisions:
                            if isinstance(d, str):
                                formatted_decisions.append(
                                    {"decision": d, "rationale": "自动生成"}
                                )
                            elif isinstance(d, dict):
                                formatted_decisions.append(d)

                        self.manifest_manager.sync_and_backfill(
                            stage_id=current_stage.id,
                            decisions=formatted_decisions,
                            completed_artifacts=artifacts,
                            next_stage=True,
                        )

                        # 重新加载上下文
                        context = self.executor.load_context()
                        self.state.update_context("stage_advanced", True)

                        # 显示新阶段信息
                        new_stage = self.manifest_manager.get_current_stage()
                        if new_stage:
                            cli.display_result(f"已推进到阶段: {new_stage.name}", True)
                        else:
                            cli.display_result("所有阶段已完成！", True)
                            return self._finalize_execution(cli, plan, "所有阶段已完成")
                except Exception as e:
                    logger.error(f"Failed to advance stage: {e}")
                    cli.display_result(f"阶段推进失败: {str(e)}", True)

                # 继续执行，不返回
                continue
            else:
                # 继续执行动作
                action_result = self.executor.act_phase(think_result)
                observation = self.executor.observe_phase(think_result, action_result)
                self.state.observations.append(observation)

            # 定期反思
            if (step + 1) % reflection_interval == 0:
                cli.display_thinking("反思执行结果...")
                reflection = self.executor.reflection_phase(self.state.observations)

                # 检查阶段是否完成（优先检查，确保阶段推进逻辑能够执行）
                if reflection.get("stage_completed"):
                    cli.display_result("阶段完成，正在推进到下一阶段...", True)

                    # 从 AgentState 中获取决策和交付物
                    decisions = self.state.get_decisions()
                    artifacts = self.state.get_artifacts()

                    logger.info(
                        f"Extracted {len(decisions)} decisions and "
                        f"{len(artifacts)} artifacts from AgentState"
                    )

                    # 推进到下一阶段
                    try:
                        current_stage = self.manifest_manager.get_current_stage()
                        if current_stage:
                            self.manifest_manager.sync_and_backfill(
                                stage_id=current_stage.id,
                                decisions=decisions,
                                completed_artifacts=artifacts,
                                next_stage=True,
                            )

                            # 清空当前阶段的决策和交付物
                            self.state.clear_decisions()
                            self.state.clear_artifacts()

                            # 重新加载上下文
                            context = self.executor.load_context()
                            self.state.update_context("stage_advanced", True)

                            # 显示新阶段信息
                            new_stage = self.manifest_manager.get_current_stage()
                            if new_stage:
                                cli.display_result(
                                    f"已推进到阶段: {new_stage.name}", True
                                )
                            else:
                                cli.display_result("所有阶段已完成！", True)
                                return self._finalize_execution(
                                    cli, plan, "所有阶段已完成"
                                )
                    except Exception as e:
                        logger.error(f"Failed to advance stage: {e}")
                        cli.display_result(f"阶段推进失败: {str(e)}", True)

                # 检查任务是否完成
                if reflection.get("task_completed"):
                    return self._finalize_execution(cli, plan, "反思确认任务完成")

        # 达到最大步数，完成执行
        return self._finalize_execution(cli, plan, "达到最大步数")

    def _finalize_execution(self, cli, plan, reason: str) -> Dict[str, Any]:
        """完成执行"""
        cli.display_result(reason, True)

        # 从 AgentState 中获取决策和交付物
        decisions = self.state.get_decisions()
        artifacts = self.state.get_artifacts()

        # 保存执行结果
        self.executor.save_execution_result(decisions, artifacts)

        # 触发阶段完成回填
        if self.manifest and hasattr(self, "manifest_manager"):
            current_stage = self.manifest_manager.get_current_stage()
            if current_stage:
                stage_id = (
                    current_stage.id
                    if hasattr(current_stage, "id")
                    else current_stage.get("id", "unknown")
                )
                self.manifest_manager.sync_and_backfill(
                    stage_id=stage_id,
                    decisions=[{"decision": d, "rationale": ""} for d in decisions]
                    if decisions
                    else [],
                    completed_artifacts=artifacts if artifacts else [],
                    next_stage=True,
                )

        # 最终反思
        cli.display_phase("Reflection Phase")
        final_reflection = self.executor.reflection_phase(self.state.observations)

        # 显示完成信息
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

    def _load_all_configs(self, config_manager: ConfigManager) -> Dict[str, Any]:
        """加载所有配置"""
        config = {"main": config_manager.get_main_config()}

        module_names = ["core", "agent", "llm", "cache", "logging", "tools"]
        for module_name in module_names:
            config[module_name] = config_manager.get_module_config(module_name)

        return config

    def _initialize_components(self):
        """传统初始化方式（向后兼容）"""
        # 这里应该实现传统初始化逻辑
        from infrastructure.llm.client import NanoLLMClient
        from application.services.router import HybridRouter
        from application.services.manifest import ManifestManager
        from spec.context import ContextLoader
        from spec.generator import SpecGenerator
        from infrastructure.persistence.manager import PersistenceManager
        from infrastructure.tools.registry import ToolRegistry

        # 从配置中读取参数
        llm_config = self.config.get("llm", {}).get("default", {})

        model = llm_config.get("model", "openai/qwen3.5-plus")

        # 初始化各个组件
        self.llm = NanoLLMClient(model=model)
        self.router = HybridRouter(self.llm)
        self.tools = ToolRegistry()
        self.manifest_manager = ManifestManager()
        self.context_loader = ContextLoader(self.manifest_manager)
        self.spec_generator = SpecGenerator(self.llm)
        self.persistence_manager = PersistenceManager()
        self.spec_initializer = SpecInitializer(
            llm_client=self.llm
        )  # 传入已有的 llm 客户端
        self.state = AgentState(self.config)

        # 创建执行器
        self.executor = AgentExecutor(
            llm_client=self.llm,
            router=self.router,
            manifest_manager=self.manifest_manager,
            context_loader=self.context_loader,
            spec_generator=self.spec_generator,
            tool_registry=self.tools,
            persistence_manager=self.persistence_manager,
            config=self.config,
            state=self.state,  # 传入 state
        )

        logger.info("NanoAgent initialized with traditional method")
