"""
NanoAgent - 主协调器（简化版）
纯粹的协调逻辑，所有业务逻辑委托给专门的模块
"""
from typing import Dict, Any, Optional
from loguru import logger
from .config import get_config_manager, ConfigManager
from .agent_state import AgentState
from .executor import AgentExecutor
from .container import DIContainer
from .spec_initializer import SpecInitializer


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
            self.spec_initializer = container.get(SpecInitializer) if container.has(SpecInitializer) else SpecInitializer()
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
        
        # 初始化CLI
        from cli_interface import get_cli
        cli = get_cli()
        cli.display_header()
        logger.info("=== Starting new task ===", task=task[:100])
        
        # === 阶段1: 路由 ===
        cli.display_phase("任务分析")
        routing_decision = self.executor.route_task(task)
        cli.display_result(f"任务类型: {routing_decision['task_type']}", True)
        cli.display_result(f"置信度: {routing_decision['confidence']:.2%}", True)
        
        # === 阶段2: Spec管理 ===
        if self.executor.should_init_spec(task, routing_decision):
            self.manifest = self.executor.init_spec(task, routing_decision, self.spec_initializer)
            if self.manifest:
                cli.display_phase("Spec 初始化")
                print("\n📋 Spec 概要")
                print(f"{'='*60}")
                print(f"项目名称: {self.manifest.project_name}")
                print(f"当前阶段: {self.manifest.current_stage}")
                print(f"总阶段数: {len(self.manifest.pipeline)}")
                print(f"{'='*60}\n")
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
    
    def _main_react_loop(self, task: str, plan, cli, context: Dict[str, Any]) -> Dict[str, Any]:
        """主ReAct循环"""
        max_steps = self.config.get("core", {}).get("performance", {}).get("max_steps", 20)
        reflection_interval = self.config.get("agent", {}).get("behavior", {}).get("reflection_interval", 5)
        
        cli.display_phase("Execution Phase")
        
        for step in range(max_steps):
            self.state.step_count = step + 1
            cli.display_progress(step + 1, max_steps, f"步骤 {step + 1}")
            
            # 重新加载上下文
            context = self.executor.load_context()
            
            # Think -> Act -> Observe
            think_result = self.executor.think_phase(task, context, self.state.observations, step)
            
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
                return self._finalize_execution(cli, plan, "阶段完成")
            else:
                # 继续执行动作
                action_result = self.executor.act_phase(think_result)
                observation = self.executor.observe_phase(think_result, action_result)
                self.state.observations.append(observation)
            
            # 定期反思
            if (step + 1) % reflection_interval == 0:
                cli.display_thinking("反思执行结果...")
                reflection = self.executor.reflection_phase(self.state.observations)
                if reflection.get("task_completed"):
                    return self._finalize_execution(cli, plan, "反思确认任务完成")
        
        # 达到最大步数，完成执行
        return self._finalize_execution(cli, plan, "达到最大步数")
    
    def _finalize_execution(self, cli, plan, reason: str) -> Dict[str, Any]:
        """完成执行"""
        cli.display_result(reason, True)
        
        # 提取决策和交付物
        decisions = self.executor.extract_decisions(self.state.observations)
        artifacts = self.executor.extract_artifacts(self.state.observations)
        
        # 保存执行结果
        self.executor.save_execution_result(decisions, artifacts)
        
        # 触发阶段完成回填
        if self.manifest and hasattr(self, 'manifest_manager'):
            current_stage = self.manifest_manager.get_current_stage()
            if current_stage:
                self.executor.init_spec("", {}, None)  # 触发阶段完成逻辑
        
        # 最终反思
        cli.display_phase("Reflection Phase")
        final_reflection = self.executor.reflection_phase(self.state.observations)
        
        # 显示完成信息
        cli.display_completion(f"执行完成 - 共 {self.state.step_count} 步")
        cli.display_footer()
        
        return {
            "status": "completed",
            "plan": plan.model_dump() if hasattr(plan, 'model_dump') else plan,
            "steps_executed": self.state.step_count,
            "observations": len(self.state.observations),
            "decisions": decisions,
            "artifacts": artifacts,
            "reflection": final_reflection,
            "message": f"Task execution completed: {reason}"
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
        # 为了简洁，这里只是占位符
        from .llm_client import NanoLLMClient
        from .router import HybridRouter
        from .manifest_manager import ManifestManager
        from spec.context import ContextLoader
        from spec.generator import SpecGenerator
        from .persistence import PersistenceManager
        from .tools.registry import ToolRegistry
        
        # 从配置中读取参数
        core_config = self.config.get("core", {}).get("performance", {})
        llm_config = self.config.get("llm", {}).get("default", {})
        
        max_steps = core_config.get("max_steps", 20)
        max_context_tokens = core_config.get("max_context_tokens", 3500)
        model = llm_config.get("model", "openai/qwen3.5-plus")
        
        # 初始化各个组件
        self.llm = NanoLLMClient(model=model)
        self.router = HybridRouter(self.llm)
        self.tools = ToolRegistry()
        self.manifest_manager = ManifestManager()
        self.context_loader = ContextLoader(self.manifest_manager)
        self.spec_generator = SpecGenerator(self.llm)
        self.persistence_manager = PersistenceManager()
        self.spec_initializer = SpecInitializer()
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
            config=self.config
        )
        
        logger.info("NanoAgent initialized with traditional method")
