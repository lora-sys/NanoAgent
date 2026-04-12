"""
上下文加载器 - NanoAgent
负责动态加载和提取 Spec 约束上下文
"""

from typing import Dict
from loguru import logger
from core.interfaces import IContextLoader


class ContextLoader(IContextLoader):
    """上下文加载器 - 从 manifest 和 spec 文件中提取上下文信息"""

    def __init__(self, manifest_manager):
        """
        初始化上下文加载器

        Args:
            manifest_manager: ManifestManager 实例
        """
        self.manifest_manager = manifest_manager
        self.current_stage_context = None

    def dynamic_load_context(self) -> Dict:
        """
        动态加载当前阶段的上下文（核心方法）

        Returns:
            包含 master_spec、current_stage_spec 和 constraints 的字典
        """
        context = {
            "master_spec": "",
            "current_stage_spec": "",
            "current_stage_id": "unknown",
            "constraints": {},  # 修复：初始化为 dict 而不是 list
        }

        try:
            # 1. 加载 manifest
            manifest = self.manifest_manager.load_manifest()
            if not manifest:
                logger.warning("No manifest found, skipping dynamic load")
                # 清除缓存的上下文以防止泄漏
                self.current_stage_context = context
                return context

            # 记录当前阶段 ID
            if hasattr(manifest, "current_stage"):
                context["current_stage_id"] = manifest.current_stage

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
                constraints = self.extract_constraints(master_spec)
                context["constraints"] = constraints

            self.current_stage_context = context
            return context

        except Exception as e:
            logger.error(f"Dynamic load failed: {e}")
            # 清除缓存的上下文以防止泄漏
            self.current_stage_context = context
            return context

    def extract_constraints(self, spec_content: str) -> Dict:
        """
        从 Spec 内容中提取约束

        Args:
            spec_content: Spec 文件内容

        Returns:
            包含 always、ask_first、never 约束的字典
        """
        constraints = {"always": [], "ask_first": [], "never": []}

        lines = spec_content.split("\n")
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

    def get_current_stage_context(self) -> Dict:
        """
        获取当前缓存的上下文

        Returns:
            当前阶段上下文字典
        """
        return self.current_stage_context or {
            "master_spec": "",
            "current_stage_spec": "",
            "constraints": {},
        }
