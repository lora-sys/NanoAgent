"""
Manifest 管理器 - NanoAgent
负责管理 manifest 的更新、状态切换和上下文回填
基于原始 templates/manifest.json 格式
"""
import os
import json
from typing import Dict, List, Optional

from .spec_initializer import Manifest, PipelineStage


class ManifestManager:
    """Manifest 管理器"""

    def __init__(self, spec_workspace_dir: str = None):
        base_dir = spec_workspace_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            ".spec"
        )
        self.manifest_path = os.path.join(base_dir, "manifest.json")
        self.master_spec_path = os.path.join(base_dir, "master_spec.md")
        self.steps_dir = os.path.join(base_dir, "steps")

    def load_manifest(self) -> Optional[Manifest]:
        """加载 manifest"""
        if not os.path.exists(self.manifest_path):
            return None

        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return Manifest(**data)

    def save_manifest(self, manifest: Manifest):
        """保存 manifest"""
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
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
            with open(stage_file, 'r', encoding='utf-8') as f:
                return f.read()

        return None

    def load_master_spec(self) -> Optional[str]:
        """加载 master spec"""
        if os.path.exists(self.master_spec_path):
            with open(self.master_spec_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def sync_and_backfill(
        self,
        stage_id: str,
        decisions: List[Dict],
        completed_artifacts: List[str],
        next_stage: bool = True
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
        print(f"\n{'='*60}")
        print(f"🔄 同步和回填 - Stage {stage_id}")
        print(f"{'='*60}\n")

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

        # 2. 回填到 master_spec
        self._backfill_to_master_spec(decisions, completed_artifacts)

        # 3. 切换到下一个阶段
        if next_stage:
            next_stage_config = self._move_to_next_stage(manifest, stage_id)
            if next_stage_config:
                print(f"  ✓ 切换到下一个阶段: {next_stage_config.id} - {next_stage_config.name}")
            else:
                print("  ✓ 所有阶段已完成！")
                manifest.status = "completed"

        # 4. 保存 manifest
        self.save_manifest(manifest)

        print("\n✅ 同步和回填完成！")
        self._print_progress_bar(manifest)

        return manifest

    def _backfill_to_master_spec(self, decisions: List[Dict], artifacts: List[str]):
        """回填到 master_spec.md"""
        print("📝 回填到 master_spec.md...")

        if not os.path.exists(self.master_spec_path):
            return

        with open(self.master_spec_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 回填决策
        if decisions:
            decisions_section = "\n### 用户决策\n"
            for decision in decisions:
                decisions_section += f"- **{decision.get('decision', '')}**: {decision.get('rationale', '')}\n"

            # 查找或添加上下文快照部分
            if "## 4. 上下文快照" in content:
                content = content.replace(
                    "## 4. 上下文快照",
                    f"## 4. 上下文快照{decisions_section}\n"
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
                lines = content.split('\n')
                in_artifacts_section = False
                for i, line in enumerate(lines):
                    if "## 3. 交付物清单" in line:
                        in_artifacts_section = True
                    elif in_artifacts_section and line.strip() == '':
                        lines.insert(i, artifacts_section)
                        break
                content = '\n'.join(lines)

        with open(self.master_spec_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("  ✓ 回填完成")

    def _move_to_next_stage(self, manifest: Manifest, current_stage_id: str) -> Optional[PipelineStage]:
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


# 使用示例
if __name__ == "__main__":
    manager = ManifestManager()

    # 模拟同步和回填
    decisions = [
        {
            "decision": "使用 JWT 认证",
            "rationale": "安全性和扩展性好"
        },
        {
            "decision": "数据库使用 PostgreSQL",
            "rationale": "需要事务支持"
        }
    ]

    artifacts = [
        "requirements.txt",
        "main.py",
        "auth.py"
    ]

    manifest = manager.sync_and_backfill(
        stage_id="stage_1",
        decisions=decisions,
        completed_artifacts=artifacts,
        next_stage=True
    )

    print(f"\n{'='*60}")
    print("📋 更新后的 Manifest")
    print(f"{'='*60}")
    print(manifest.model_dump_json(indent=2))
