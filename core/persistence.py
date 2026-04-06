"""
持久化层 - NanoAgent
负责管理所有文件的读写操作，提供统一的持久化接口
"""
import os
import json
from typing import Optional, Dict, List, Any
from datetime import datetime
from loguru import logger
from pathlib import Path


class PersistenceManager:
    """持久化管理器 - 统一文件读写操作"""

    def __init__(self, base_dir: str = None):
        """
        初始化持久化管理器

        Args:
            base_dir: 基础目录，默认为 .spec
        """
        if base_dir is None:
            base_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                ".spec"
            )
        self.base_dir = Path(base_dir)
        self.ensure_directories()

    def ensure_directories(self):
        """确保所有必要的目录存在"""
        directories = [
            self.base_dir,
            self.base_dir / "steps",
            self.base_dir / "context"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def read_json(self, relative_path: str) -> Optional[Dict]:
        """
        读取 JSON 文件

        Args:
            relative_path: 相对于 base_dir 的路径

        Returns:
            解析后的 JSON 字典，如果文件不存在则返回 None
        """
        file_path = self.base_dir / relative_path
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read JSON file {file_path}: {e}")
            return None

    def write_json(self, relative_path: str, data: Dict, indent: int = 2):
        """
        写入 JSON 文件

        Args:
            relative_path: 相对于 base_dir 的路径
            data: 要写入的数据
            indent: JSON 缩进
        """
        file_path = self.base_dir / relative_path
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            logger.info(f"✓ Wrote JSON: {relative_path}")
        except Exception as e:
            logger.error(f"Failed to write JSON file {file_path}: {e}")

    def read_text(self, relative_path: str) -> Optional[str]:
        """
        读取文本文件

        Args:
            relative_path: 相对于 base_dir 的路径

        Returns:
            文件内容，如果文件不存在则返回 None
        """
        file_path = self.base_dir / relative_path
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read text file {file_path}: {e}")
            return None

    def write_text(self, relative_path: str, content: str):
        """
        写入文本文件

        Args:
            relative_path: 相对于 base_dir 的路径
            content: 要写入的内容
        """
        file_path = self.base_dir / relative_path
        try:
            # 确保父目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"✓ Wrote text: {relative_path}")
        except Exception as e:
            logger.error(f"Failed to write text file {file_path}: {e}")

    def append_text(self, relative_path: str, content: str):
        """
        追加文本到文件

        Args:
            relative_path: 相对于 base_dir 的路径
            content: 要追加的内容
        """
        file_path = self.base_dir / relative_path
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"✓ Appended to: {relative_path}")
        except Exception as e:
            logger.error(f"Failed to append to text file {file_path}: {e}")

    def exists(self, relative_path: str) -> bool:
        """
        检查文件是否存在

        Args:
            relative_path: 相对于 base_dir 的路径

        Returns:
            文件是否存在
        """
        file_path = self.base_dir / relative_path
        return file_path.exists()

    def delete(self, relative_path: str):
        """
        删除文件

        Args:
            relative_path: 相对于 base_dir 的路径
        """
        file_path = self.base_dir / relative_path
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"✓ Deleted: {relative_path}")
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")

    def list_files(self, relative_path: str = "", pattern: str = "*") -> List[str]:
        """
        列出目录中的文件

        Args:
            relative_path: 相对于 base_dir 的路径
            pattern: 文件匹配模式

        Returns:
            文件名列表
        """
        dir_path = self.base_dir / relative_path
        if not dir_path.exists():
            return []

        try:
            return [f.name for f in dir_path.glob(pattern) if f.is_file()]
        except Exception as e:
            logger.error(f"Failed to list files in {dir_path}: {e}")
            return []

    def backup(self, relative_path: str, backup_suffix: str = None):
        """
        备份文件

        Args:
            relative_path: 相对于 base_dir 的路径
            backup_suffix: 备份文件后缀，默认为时间戳
        """
        if backup_suffix is None:
            backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")

        file_path = self.base_dir / relative_path
        if not file_path.exists():
            logger.warning(f"File not found for backup: {relative_path}")
            return

        backup_path = file_path.with_suffix(f"{file_path.suffix}.bak_{backup_suffix}")
        try:
            import shutil
            shutil.copy2(file_path, backup_path)
            logger.info(f"✓ Backed up: {relative_path} -> {backup_path.name}")
        except Exception as e:
            logger.error(f"Failed to backup file {file_path}: {e}")

    def restore(self, relative_path: str, backup_suffix: str):
        """
        从备份恢复文件

        Args:
            relative_path: 相对于 base_dir 的路径
            backup_suffix: 备份文件后缀
        """
        file_path = self.base_dir / relative_path
        backup_path = file_path.with_suffix(f"{file_path.suffix}.bak_{backup_suffix}")

        if not backup_path.exists():
            logger.warning(f"Backup not found: {backup_path.name}")
            return

        try:
            import shutil
            shutil.copy2(backup_path, file_path)
            logger.info(f"✓ Restored: {relative_path} from {backup_path.name}")
        except Exception as e:
            logger.error(f"Failed to restore file {file_path}: {e}")

    def get_absolute_path(self, relative_path: str) -> str:
        """
        获取文件的绝对路径

        Args:
            relative_path: 相对于 base_dir 的路径

        Returns:
            绝对路径
        """
        return str(self.base_dir / relative_path)

    def get_base_dir(self) -> str:
        """
        获取基础目录

        Returns:
            基础目录的绝对路径
        """
        return str(self.base_dir)