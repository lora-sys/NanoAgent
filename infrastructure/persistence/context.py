"""
上下文管理器 - NanoAgent
持久化上下文管理，支持跨会话恢复和增量更新
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from loguru import logger


class ContextManager:
    """持久化上下文管理器

    功能：
    - 保存阶段上下文到文件
    - 加载阶段上下文
    - 增量更新上下文
    - 支持跨会话恢复
    """

    def __init__(self, context_dir: str = ".spec/context"):
        """
        初始化上下文管理器

        Args:
            context_dir: 上下文目录路径
        """
        self.context_dir = Path(context_dir)
        self.context_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ ContextManager initialized with dir: {self.context_dir}")

    def save_context(self, stage_id: str, context: Dict) -> None:
        """
        保存阶段上下文

        Args:
            stage_id: 阶段 ID（如：stage_1）
            context: 上下文字典
        """
        try:
            # 添加元数据
            context["metadata"] = {
                "stage_id": stage_id,
                "updated_at": datetime.now().isoformat(),
            }

            context_file = self.context_dir / f"{stage_id}.json"

            with open(context_file, "w", encoding="utf-8") as f:
                json.dump(context, f, indent=2, ensure_ascii=False)

            logger.info(f"✓ 保存上下文: {stage_id} -> {context_file}")

        except Exception as e:
            logger.error(f"保存上下文失败 {stage_id}: {e}")
            raise

    def load_context(self, stage_id: str) -> Optional[Dict]:
        """
        加载阶段上下文

        Args:
            stage_id: 阶段 ID（如：stage_1）

        Returns:
            上下文字典，如果不存在则返回 None
        """
        try:
            context_file = self.context_dir / f"{stage_id}.json"

            if not context_file.exists():
                logger.debug(f"⚠️ 上下文文件不存在: {context_file}")
                return None

            with open(context_file, "r", encoding="utf-8") as f:
                context = json.load(f)

            logger.info(f"✓ 加载上下文: {stage_id} <- {context_file}")
            return context

        except Exception as e:
            logger.error(f"加载上下文失败 {stage_id}: {e}")
            return None

    def update_context(self, stage_id: str, updates: Dict) -> None:
        """
        增量更新上下文

        Args:
            stage_id: 阶段 ID（如：stage_1）
            updates: 要更新的字段
        """
        try:
            # 加载现有上下文
            context = self.load_context(stage_id)

            if context is None:
                # 如果不存在，创建新的上下文
                context = {
                    "master_spec": "",
                    "current_stage_spec": "",
                    "constraints": {},
                    "collected_info": {
                        "requirements": {},
                        "decisions": [],
                        "artifacts": [],
                    },
                    "execution_state": {
                        "step_count": 0,
                        "last_action": "",
                        "last_observation": "",
                    },
                }

            # 深度合并更新
            context = self._deep_merge(context, updates)

            # 保存更新后的上下文
            self.save_context(stage_id, context)

            logger.info(f"✓ 更新上下文: {stage_id}")

        except Exception as e:
            logger.error(f"更新上下文失败 {stage_id}: {e}")
            raise

    def delete_context(self, stage_id: str) -> None:
        """
        删除阶段上下文

        Args:
            stage_id: 阶段 ID（如：stage_1）
        """
        try:
            context_file = self.context_dir / f"{stage_id}.json"

            if context_file.exists():
                context_file.unlink()
                logger.info(f"✓ 删除上下文: {stage_id}")

        except Exception as e:
            logger.error(f"删除上下文失败 {stage_id}: {e}")
            raise

    def list_contexts(self) -> list[str]:
        """
        列出所有保存的上下文

        Returns:
            阶段 ID 列表
        """
        try:
            contexts = []
            for context_file in self.context_dir.glob("*.json"):
                stage_id = context_file.stem
                contexts.append(stage_id)

            return sorted(contexts)

        except Exception as e:
            logger.error(f"列出上下文失败: {e}")
            return []

    def clear_all_contexts(self) -> None:
        """清除所有上下文"""
        try:
            for context_file in self.context_dir.glob("*.json"):
                context_file.unlink()

            logger.info("✓ 清除所有上下文")

        except Exception as e:
            logger.error(f"清除上下文失败: {e}")
            raise

    def _deep_merge(self, base: Dict, updates: Dict) -> Dict:
        """
        深度合并字典

        Args:
            base: 基础字典
            updates: 更新字典

        Returns:
            合并后的字典
        """
        result = base.copy()

        for key, value in updates.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                # 递归合并嵌套字典
                result[key] = self._deep_merge(result[key], value)
            elif (
                key in result
                and isinstance(result[key], list)
                and isinstance(value, list)
            ):
                # 合并列表（去重）
                result[key] = list(set(result[key] + value))
            else:
                # 直接替换
                result[key] = value

        return result

    def get_context_info(self, stage_id: str) -> Optional[Dict]:
        """
        获取上下文信息（不加载完整内容）

        Args:
            stage_id: 阶段 ID（如：stage_1）

        Returns:
            上下文信息字典
        """
        try:
            context = self.load_context(stage_id)

            if context is None:
                return None

            metadata = context.get("metadata", {})

            return {
                "stage_id": stage_id,
                "updated_at": metadata.get("updated_at"),
                "has_master_spec": bool(context.get("master_spec")),
                "has_current_stage_spec": bool(context.get("current_stage_spec")),
                "decisions_count": len(
                    context.get("collected_info", {}).get("decisions", [])
                ),
                "artifacts_count": len(
                    context.get("collected_info", {}).get("artifacts", [])
                ),
                "step_count": context.get("execution_state", {}).get("step_count", 0),
            }

        except Exception as e:
            logger.error(f"获取上下文信息失败 {stage_id}: {e}")
            return None
