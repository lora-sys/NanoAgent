"""
Manifest 管理器 - NanoAgent
负责管理 manifest 的更新、状态切换和上下文回填
基于原始 templates/manifest.json 格式
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from .spec_initializer import Manifest, PipelineStage


class ManifestManager:
    """Manifest 管理器"""

    def __init__(self, spec_workspace_dir: str = None):
        base_dir = spec_workspace_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".spec"
        )
        self.manifest_path = os.path.join(base_dir, "manifest.json")
        self.master_spec_path = os.path.join(base_dir, "master_spec.md")
        self.steps_dir = os.path.join(base_dir, "steps")

    def load_manifest(self) -> Optional[Manifest]:
        """加载 manifest"""
        if not os.path.exists(self.manifest_path):
            return None

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return Manifest(**data)

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
        """
        同步和回填 - 核心功能

        Args:
            stage_id: 当前阶段 ID
            decisions: 决策列表 [{"decision": "...", "rationale": "..."}]
            completed_artifacts: 完成的产出物列表
            next_stage: 是否切换到下一个阶段

        Returns:
            Manifest: 更新后的 manifest
        """
        print(f"\n{'=' * 60}")
        print(f"🔄 同步和回填 - Stage {stage_id}")
        print(f"{'=' * 60}\n")

        manifest = self.load_manifest()
        if not manifest:
            raise ValueError("Manifest 不存在，请先初始化 Spec")

        # 1. 标记当前阶段为 completed
        current_stage = None
        for stage in manifest.pipeline:
            if stage.id == stage_id:
                stage.status = "completed"
                current_stage = stage
                break

        if not current_stage:
            raise ValueError(f"阶段 {stage_id} 不存在")

        # 2. 更新 ContextManager 中的上下文
        self._update_context_manager(stage_id, decisions, completed_artifacts)

        # 3. 回填到 master_spec
        self._backfill_to_master_spec(decisions, completed_artifacts)

        # 4. 更新 Steps 文件的状态
        self._update_steps_file_status(stage_id, "completed")

        # 5. 切换到下一个阶段
        if next_stage:
            next_stage_config = self._move_to_next_stage(manifest, stage_id)
            if next_stage_config:
                print(
                    f"  ✓ 切换到下一个阶段: {next_stage_config.id} - {next_stage_config.name}"
                )
                # 更新下一个阶段的 Steps 文件状态为 active
                self._update_steps_file_status(next_stage_config.id, "active")
            else:
                print("  ✓ 所有阶段已完成！")
                manifest.status = "completed"

        # 6. 保存 manifest
        self.save_manifest(manifest)

        print("\n✅ 同步和回填完成！")
        self._print_progress_bar(manifest)

        return manifest

    def _backfill_to_master_spec(self, decisions: List[Dict], artifacts: List[str]):
        """回填到 master_spec.md"""
        print("📝 回填到 master_spec.md...")

        if not os.path.exists(self.master_spec_path):
            return

        with open(self.master_spec_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 回填决策
        if decisions:
            decisions_section = "\n### 用户决策\n"
            for decision in decisions:
                decisions_section += f"- **{decision.get('decision', '')}**: {decision.get('rationale', '')}\n"

            # 查找或添加上下文快照部分
            if "## 4. 上下文快照" in content:
                content = content.replace(
                    "## 4. 上下文快照", f"## 4. 上下文快照{decisions_section}\n"
                )
            else:
                content += f"\n## 4. 上下文快照{decisions_section}\n"

        # 回填产出物
        if artifacts:
            artifacts_section = "\n### 已完成的产出物\n"
            for artifact in artifacts:
                artifacts_section += f"- [x] {artifact}\n"

            if "## 3. 交付物清单" in content:
                # 查找并更新交付物清单
                lines = content.split("\n")
                in_artifacts_section = False
                for i, line in enumerate(lines):
                    if "## 3. 交付物清单" in line:
                        in_artifacts_section = True
                    elif in_artifacts_section and line.strip() == "":
                        lines.insert(i, artifacts_section)
                        break
                content = "\n".join(lines)

        with open(self.master_spec_path, "w", encoding="utf-8") as f:
            f.write(content)

        print("  ✓ 回填完成")

    def _move_to_next_stage(
        self, manifest: Manifest, current_stage_id: str
    ) -> Optional[PipelineStage]:
        """移动到下一个阶段"""
        # 找到当前阶段的索引
        current_index = -1
        for i, stage in enumerate(manifest.pipeline):
            if stage.id == current_stage_id:
                current_index = i
                break

        if current_index == -1 or current_index == len(manifest.pipeline) - 1:
            return None

        # 激活下一个阶段
        next_stage = manifest.pipeline[current_index + 1]
        next_stage.status = "active"
        manifest.current_stage = next_stage.id

        return next_stage

    def _print_progress_bar(self, manifest: Manifest):
        """打印进度条"""
        total = len(manifest.pipeline)
        completed = sum(1 for stage in manifest.pipeline if stage.status == "completed")

        progress = (completed / total) * 100 if total > 0 else 0
        filled = int(progress / 10)
        bar = "█" * filled + "░" * (10 - filled)

        print(f"\n📊 进度: [{bar}] {progress:.0f}%")
        print(f"   已完成: {completed}/{total}")
        print(f"   当前: {manifest.current_stage}\n")

    def check_task_completion(self) -> bool:
        """检查任务是否完成"""
        manifest = self.load_manifest()
        if not manifest:
            return False

        return all(stage.status == "completed" for stage in manifest.pipeline)

    def get_stage_info(self, stage_id: str) -> Optional[Dict]:
        """获取阶段信息"""
        manifest = self.load_manifest()
        if not manifest:
            return None

        for stage in manifest.pipeline:
            if stage.id == stage_id:
                return stage.model_dump()

        return None

    def _update_context_manager(
        self, stage_id: str, decisions: List[Dict], artifacts: List[str]
    ):
        """更新 ContextManager 中的上下文"""
        print("📝 更新 ContextManager 上下文...")

        try:
            from .context_manager import ContextManager

            context_manager = ContextManager()

            # 加载 master_spec 和当前阶段 spec
            master_spec = self.load_master_spec() or ""
            current_stage_spec = self.load_current_stage_spec() or ""

            # 构建更新数据
            updates = {
                "master_spec": master_spec,
                "current_stage_spec": current_stage_spec,
                "collected_info": {
                    "decisions": decisions,
                    "artifacts": artifacts,
                },
            }

            # 更新上下文
            context_manager.update_context(stage_id, updates)
            print(f"  ✓ 上下文已更新: {stage_id}")

        except Exception as e:
            print(f"  ⚠️ 上下文更新失败: {e}")

    def _update_steps_file_status(self, stage_id: str, status: str):
        """更新 Steps 文件的状态"""
        print(f"📝 更新 Steps 文件状态: {stage_id} -> {status}")

        try:
            manifest = self.load_manifest()
            if not manifest:
                return

            # 找到对应的 stage
            stage = None
            for s in manifest.pipeline:
                if s.id == stage_id:
                    stage = s
                    break

            if not stage:
                print(f"  ⚠️ 阶段 {stage_id} 不存在")
                return

            # 读取 steps 文件
            stage_file = os.path.join(self.steps_dir, stage.file)
            if not os.path.exists(stage_file):
                print(f"  ⚠️ 文件不存在: {stage_file}")
                return

            with open(stage_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 更新状态行
            status_pattern = r"\*\*状态\*\*:\s*\w+"
            status_line = f"**状态**: {status}"

            if re.search(status_pattern, content):
                content = re.sub(status_pattern, status_line, content)
            else:
                # 如果没有状态行，添加到文件末尾
                content += f"\n\n---\n\n**状态**: {status}\n**更新时间**: {datetime.now().isoformat()}\n"

            # 保存文件
            with open(stage_file, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"  ✓ 文件状态已更新: {stage_file}")

        except Exception as e:
            print(f"  ⚠️ 文件状态更新失败: {e}")

    def get_progress_bar(self) -> Any:
        """获取进度条对象。

        Returns:
            进度条对象。当前返回 None，
            可由外部 UI 组件替换。
        """
        return None

    def save(self, decisions: List[Dict] = None, artifacts: List[str] = None):
        """保存执行结果到 Manifest。

        这是一个便捷方法，将决策和交付物更新到当前 Manifest 并保存。

        Args:
            decisions: 决策列表。
            artifacts: 完成的交付物列表。
        """
        manifest = self.load_manifest()
        if manifest:
            if artifacts or decisions:
                # 更新当前阶段 pipeline 状态
                current_stage = self.get_current_stage()
                if current_stage and hasattr(manifest, "pipeline"):
                    for stage in manifest.pipeline:
                        if stage.id == current_stage.id:
                            if artifacts:
                                stage.completed_steps = len(artifacts)
                            break
            self.save_manifest(manifest)


# 使用示例
if __name__ == "__main__":
    manager = ManifestManager()

    # 模拟同步和回填
    decisions = [
        {"decision": "使用 JWT 认证", "rationale": "安全性和扩展性好"},
        {"decision": "数据库使用 PostgreSQL", "rationale": "需要事务支持"},
    ]

    artifacts = ["requirements.txt", "main.py", "auth.py"]

    manifest = manager.sync_and_backfill(
        stage_id="stage_1",
        decisions=decisions,
        completed_artifacts=artifacts,
        next_stage=True,
    )

    print(f"\n{'=' * 60}")
    print("📋 更新后的 Manifest")
    print(f"{'=' * 60}")
    print(manifest.model_dump_json(indent=2))
