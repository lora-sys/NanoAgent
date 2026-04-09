"""
核心接口定义 - NanoAgent
定义系统中所有关键组件的接口契约
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from spec.models import TaskSpec, RoutingDecision, Manifest


class ILLMClient(ABC):
    """LLM 客户端接口"""

    @abstractmethod
    def chat(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """
        聊天对话

        Args:
            messages: 消息列表
            temperature: 温度参数

        Returns:
            LLM 响应内容
        """
        pass

    @abstractmethod
    def structured_chat(self, messages: List[Dict], response_model: Any, temperature: float = 0.7) -> Any:
        """
        结构化聊天对话

        Args:
            messages: 消息列表
            response_model: 响应模型
            temperature: 温度参数

        Returns:
            结构化响应对象
        """
        pass


class IContextLoader(ABC):
    """上下文加载器接口"""

    @abstractmethod
    def dynamic_load_context(self) -> Dict:
        """
        动态加载当前阶段的上下文

        Returns:
            包含 master_spec、current_stage_spec 和 constraints 的字典
        """
        pass

    @abstractmethod
    def extract_constraints(self, spec_content: str) -> Dict:
        """
        从 Spec 内容中提取约束

        Args:
            spec_content: Spec 文件内容

        Returns:
            包含 always、ask_first、never 约束的字典
        """
        pass

    @abstractmethod
    def get_current_stage_context(self) -> Dict:
        """
        获取当前缓存的上下文

        Returns:
            当前阶段上下文字典
        """
        pass


class ISpecGenerator(ABC):
    """Spec 生成器接口"""

    @abstractmethod
    def generate_spec(self, task: str) -> TaskSpec:
        """
        根据用户任务生成高质量 Spec

        Args:
            task: 用户任务描述

        Returns:
            生成的 TaskSpec 对象
        """
        pass


class IRouter(ABC):
    """路由器接口"""

    @abstractmethod
    def route(self, user_input: str) -> RoutingDecision:
        """
        基于规则进行路由

        Args:
            user_input: 用户输入

        Returns:
            路由决策，总是返回有效的 RoutingDecision
        """
        pass


class IManifestManager(ABC):
    """Manifest 管理器接口"""

    @abstractmethod
    def load_manifest(self) -> Optional[Manifest]:
        """
        加载 manifest

        Returns:
            Manifest 对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def save_manifest(self, manifest: Manifest):
        """
        保存 manifest

        Args:
            manifest: Manifest 对象
        """
        pass

    @abstractmethod
    def get_current_stage(self) -> Optional[Dict]:
        """
        获取当前活动的阶段

        Returns:
            当前阶段字典，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def load_current_stage_spec(self) -> Optional[str]:
        """
        加载当前阶段的 spec

        Returns:
            Spec 内容，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def sync_and_backfill(
        self,
        stage_id: str,
        decisions: List[Dict[str, Any]],
        completed_artifacts: List[str],
        next_stage: bool = True
    ) -> Optional["Manifest"]:
        """同步和回填

        Args:
            stage_id: 当前阶段 ID
            decisions: 决策列表
            completed_artifacts: 完成的产出物列表
            next_stage: 是否切换到下一个阶段
            
        Returns:
            更新后的 manifest，如果失败则返回 None
        """
        pass

    @abstractmethod
    def get_progress_bar(self) -> Any:
        """获取进度条对象

        Returns:
            进度条对象，具体类型取决于实现
        """
        pass

    @abstractmethod
    def load_master_spec(self) -> Optional[str]:
        """
        加载 master spec

        Returns:
            Master spec 内容，如果不存在则返回 None
        """
        pass


class IPersistenceManager(ABC):
    """持久化管理器接口"""

    @abstractmethod
    def read_json(self, relative_path: str) -> Optional[Dict]:
        """
        读取 JSON 文件

        Args:
            relative_path: 相对于基础目录的路径

        Returns:
            解析后的 JSON 字典，如果文件不存在则返回 None
        """
        pass

    @abstractmethod
    def write_json(self, relative_path: str, data: Dict, indent: int = 2):
        """
        写入 JSON 文件

        Args:
            relative_path: 相对于基础目录的路径
            data: 要写入的数据
            indent: JSON 缩进
        """
        pass

    @abstractmethod
    def read_text(self, relative_path: str) -> Optional[str]:
        """
        读取文本文件

        Args:
            relative_path: 相对于基础目录的路径

        Returns:
            文件内容，如果文件不存在则返回 None
        """
        pass

    @abstractmethod
    def write_text(self, relative_path: str, content: str):
        """
        写入文本文件

        Args:
            relative_path: 相对于基础目录的路径
            content: 要写入的内容
        """
        pass

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """
        检查文件是否存在

        Args:
            relative_path: 相对于基础目录的路径

        Returns:
            文件是否存在
        """
        pass

    @abstractmethod
    def get_base_dir(self) -> str:
        """
        获取基础目录

        Returns:
            基础目录的绝对路径
        """
        pass


class IToolRegistry(ABC):
    """工具注册表接口"""

    @abstractmethod
    def execute(self, name: str, arguments: Dict) -> Any:
        """
        执行工具

        Args:
            name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        pass

    @abstractmethod
    def get_available_tools(self) -> List[str]:
        """
        获取可用工具列表

        Returns:
            工具名称列表
        """
        pass