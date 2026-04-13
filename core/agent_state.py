"""Agent State Management - Data-Driven (Manifest Source of Truth).

不再维护内存中的 StateMachine。状态完全由 manifest.json 驱动。
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger


class AgentState:
    """Agent 状态管理器，直接读写 manifest.json。"""

    def __init__(self, manifest_path: str = ".spec/manifest.json"):
        self.manifest_path = manifest_path
        self._memory_cache: Optional[Dict] = None
        
        # 运行时内存数据 (Runtime Memory)
        self.step_count = 0
        self.observations = []
        self.decisions = []
        self.artifacts = []
        self.messages = []
        self.current_plan = None

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def _load_manifest(self) -> Dict:
        """从文件加载 Manifest"""
        if self._memory_cache:
            return self._memory_cache

        if not os.path.exists(self.manifest_path):
            return {}

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                self._memory_cache = json.load(f)
            return self._memory_cache
        except Exception as e:
            logger.error(f"加载 manifest.json 失败: {e}")
            return {}

    def _save_manifest(self, data: Dict):
        """保存 Manifest 到文件"""
        self._memory_cache = data
        try:
            os.makedirs(os.path.dirname(self.manifest_path), exist_ok=True)
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存 manifest.json 失败: {e}")

    @property
    def current_stage(self) -> str:
        """获取当前阶段 ID (直接读取 Manifest)"""
        manifest = self._load_manifest()
        return manifest.get("current_stage", "unknown")

    @property
    def status(self) -> str:
        """获取当前状态"""
        manifest = self._load_manifest()
        return manifest.get("status", "initializing")

    @property
    def pipeline(self) -> List[Dict]:
        """获取流水线阶段列表"""
        manifest = self._load_manifest()
        return manifest.get("pipeline", [])

    def get_stage_status(self, stage_id: str) -> str:
        """获取指定阶段的状态"""
        for stage in self.pipeline:
            if stage.get("id") == stage_id:
                return stage.get("status", "pending")
        return "missing"

    def update_stage_status(self, stage_id: str, status: str):
        """更新阶段状态并持久化"""
        manifest = self._load_manifest()
        manifest["current_stage"] = stage_id
        
        # 更新 pipeline 中的状态
        for stage in manifest.get("pipeline", []):
            if stage.get("id") == stage_id:
                stage["status"] = status
            else:
                # 其他阶段标记为 pending
                if stage.get("status") == "active":
                    stage["status"] = "pending"
        
        self._save_manifest(manifest)
        logger.info(f"✅ 状态更新: Stage {stage_id} -> {status}")

    # --- 运行时内存数据 (不写入 Manifest 的临时数据) ---

    def add_artifact(self, path: str, description: str = "", step: int = None):
        self.artifacts.append({"path": path, "description": description})
        logger.info(f"📦 Artifact added: {path}")

    def get_artifacts(self) -> List[str]:
        return [a["path"] for a in self.artifacts]

    def add_decision(self, decision: str):
        self.decisions.append(decision)

    def get_decisions(self) -> List[str]:
        return [str(d) for d in self.decisions]

    def get_requirements_summary(self) -> str:
        """从 Manifest 或内存中获取需求摘要"""
        manifest = self._load_manifest()
        reqs = manifest.get("process_requirements", [])
        return "\n".join(reqs) if isinstance(reqs, list) else str(reqs)

    def is_requirements_confirmed(self) -> bool:
        """判断需求是否已确认"""
        # 如果 Manifest 存在且状态不是 initializing，则视为已确认
        manifest = self._load_manifest()
        return manifest.get("status") != "initializing"

    def get_current_state(self):
        """兼容旧接口，返回一个伪状态对象"""
        class StateObj:
            def __init__(self, status): self.value = status
        return StateObj(self.status)
    # 如果需要存 observations/decisions，可以存在 manifest 里，或者单独的文件。
    # 为了简单，这里演示如何存入 manifest 的 custom 字段。

    def add_execution_record(self, record_type: str, data: Any):
        """添加执行记录到 Manifest (可选)"""
        manifest = self._load_manifest()
        if "execution_log" not in manifest:
            manifest["execution_log"] = []
        manifest["execution_log"].append({"type": record_type, "data": data})
        self._save_manifest(manifest)

    def reset(self):
        """重置状态：删除 Manifest 和缓存"""
        self._memory_cache = None
        if os.path.exists(self.manifest_path):
            try:
                os.remove(self.manifest_path)
                logger.info(f"🧹 已重置状态: 删除 {self.manifest_path}")
            except Exception as e:
                logger.warning(f"删除 Manifest 失败: {e}")
