"""
Manifest 管理器 - NanoAgent
负责管理 manifest 的更新、状态切换和上下文回填
"""

import os
import json
from typing import Dict, List, Optional
from .spec_initializer import Manifest, PipelineStage
from loguru import logger


class ManifestManager:
    def __init__(self, spec_workspace_dir: str = None):
        base_dir = spec_workspace_dir or os.path.join(os.getcwd(), ".spec")
        self.manifest_path = os.path.join(base_dir, "manifest.json")
        self.master_spec_path = os.path.join(base_dir, "master_spec.md")
        self.steps_dir = os.path.join(base_dir, "steps")

    def load_manifest(self) -> Optional[Manifest]:
        """加载 manifest"""
        if not os.path.exists(self.manifest_path):
            return None
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            return Manifest(**json.load(f))

    def save_manifest(self, manifest: Manifest):
        """保存 manifest"""
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

    def get_current_stage(self) -> Optional[PipelineStage]:
        """获取当前活动的阶段"""
        manifest = self.load_manifest()
        if not manifest:
            return None
        for stage in manifest.pipeline:
            if stage.status == "active":
                return stage
        return None

    def load_current_stage_spec(self) -> Optional[str]:
        """加载当前阶段的 spec"""
        stage = self.get_current_stage()
        if not stage:
            return None
        stage_file = os.path.join(self.steps_dir, stage.file)
        if os.path.exists(stage_file):
            with open(stage_file, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def load_master_spec(self) -> Optional[str]:
        """加载 master spec"""
        if os.path.exists(self.master_spec_path):
            with open(self.master_spec_path, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def sync_and_backfill(
        self,
        stage_id: str,
        decisions: List[Dict],
        completed_artifacts: List[str],
        next_stage: bool = True,
    ) -> Manifest:
        """同步状态并回填到下一阶段"""
        manifest = self.load_manifest()
        if not manifest:
            raise ValueError("Manifest 不存在，请先初始化 Spec")

        # 标记当前阶段为 completed
        current_stage = None
        for stage in manifest.pipeline:
            if stage.id == stage_id:
                stage.status = "completed"
                current_stage = stage
                break

        if not current_stage:
            raise ValueError(f"阶段 {stage_id} 不存在")

        # 更新上下文
        self._update_context(stage_id, decisions, completed_artifacts)

        # 回填到 master_spec
        self._backfill_master_spec(decisions, completed_artifacts)

        # 切换到下一个阶段
        if next_stage:
            next_stage = self._move_to_next_stage(manifest, stage_id)
            if next_stage:
                logger.info(f"切换到下一阶段: {next_stage.id} - {next_stage.name}")
            else:
                logger.info("所有阶段已完成")
                manifest.status = "completed"

        self.save_manifest(manifest)
        return manifest

    def _backfill_master_spec(self, decisions: List[Dict], artifacts: List[str]):
        """回填决策和产出物到 master_spec"""
        if not os.path.exists(self.master_spec_path):
            return

        with open(self.master_spec_path, "r", encoding="utf-8") as f:
            content = f.read()

        if decisions:
            section = "\n### 决策记录\n" + "\n".join(
                f"- {d.get('decision', '')}: {d.get('rationale', '')}" for d in decisions
            )
            content += section

        if artifacts:
            section = "\n### 产出物\n" + "\n".join(f"- [x] {a}" for a in artifacts)
            content += section

        with open(self.master_spec_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _move_to_next_stage(
        self, manifest: Manifest, current_stage_id: str
    ) -> Optional[PipelineStage]:
        """移动到下一个阶段"""
        for i, stage in enumerate(manifest.pipeline):
            if stage.id == current_stage_id and i < len(manifest.pipeline) - 1:
                next_stage = manifest.pipeline[i + 1]
                next_stage.status = "active"
                manifest.current_stage = next_stage.id
                return next_stage
        return None

    def _update_context(self, stage_id: str, decisions: List[Dict], artifacts: List[str]):
        """更新阶段上下文"""
        try:
            from infrastructure.persistence.context import ContextManager
            context_manager = ContextManager()

            master_spec = self.load_master_spec() or ""
            current_stage_spec = self.load_current_stage_spec() or ""

            context_manager.update_context(stage_id, {
                "master_spec": master_spec,
                "current_stage_spec": current_stage_spec,
                "decisions": decisions,
                "artifacts": artifacts,
            })
        except Exception as e:
            logger.warning(f"上下文更新失败: {e}")

    def save(self, decisions: List[Dict] = None, artifacts: List[str] = None):
        """保存执行结果到 Manifest"""
        manifest = self.load_manifest()
        if manifest:
            self.save_manifest(manifest)
