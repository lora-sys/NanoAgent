"""
Spec 初始化器 - NanoAgent
负责创建 Spec 结构、生成 manifest 和初始化步骤
"""

import os
import re
from typing import Dict, List
from datetime import datetime
from domain.models.models import PipelineStage, Manifest, TemplateSpecContent
from infrastructure.llm.client import NanoLLMClient
from loguru import logger

# 任务类型 -> 阶段定义
PIPELINE_MAP = {
    "code": [
        {"id": "stage_1", "name": "需求对齐", "file": "01_requirements.md"},
        {"id": "stage_2", "name": "接口设计", "file": "02_api_design.md"},
        {"id": "stage_3", "name": "逻辑实现", "file": "03_implementation.md"},
        {"id": "stage_4", "name": "测试计划", "file": "04_testing.md"},
        {"id": "stage_5", "name": "部署指南", "file": "05_deployment.md"},
    ],
    "writing": [
        {"id": "stage_1", "name": "大纲规划", "file": "01_outline.md"},
        {"id": "stage_2", "name": "内容撰写", "file": "02_content.md"},
        {"id": "stage_3", "name": "编辑润色", "file": "03_edit.md"},
        {"id": "stage_4", "name": "发布准备", "file": "04_publish.md"},
    ],
    "analyze": [
        {"id": "stage_1", "name": "范围定义", "file": "01_scope.md"},
        {"id": "stage_2", "name": "分析执行", "file": "02_analysis.md"},
        {"id": "stage_3", "name": "发现总结", "file": "03_findings.md"},
        {"id": "stage_4", "name": "建议提出", "file": "04_recommendations.md"},
    ],
    "chat": [
        {"id": "stage_1", "name": "理解意图", "file": "01_understand.md"},
        {"id": "stage_2", "name": "深入讨论", "file": "02_discuss.md"},
        {"id": "stage_3", "name": "总结记录", "file": "03_summarize.md"},
    ],
}

STAGE_DESC = {
    "stage_1": "明确需求和目标",
    "stage_2": "设计和规划",
    "stage_3": "实现和执行",
    "stage_4": "测试和验证",
    "stage_5": "部署和交付",
}

STEP_TEMPLATE = """# {name}

## 阶段 ID
{id}

## 描述
{desc}

## 成功标准
{criteria}

---

**状态**: {status}
**创建时间**: {time}
"""


class SpecInitializer:
    def __init__(self, base_dir: str = None, llm_client=None):
        self.base_dir = base_dir or os.getcwd()
        self.templates_dir = os.path.join(self.base_dir, "templates", "moubles")
        self.spec_workspace_dir = os.path.join(self.base_dir, ".spec")
        self.llm = llm_client or NanoLLMClient()

    def init_spec(self, task: str, routing_decision) -> Manifest:
        """初始化 Spec"""
        self._create_dirs()
        project_name = self._generate_project_name(task)
        self._load_and_fill_templates(task, routing_decision, project_name)
        pipeline = self._create_pipeline(routing_decision.task_type, task)
        return self._create_manifest(project_name, pipeline)

    def _create_dirs(self):
        for d in [self.spec_workspace_dir, os.path.join(self.spec_workspace_dir, "steps")]:
            os.makedirs(d, exist_ok=True)

    def _generate_project_name(self, task: str) -> str:
        try:
            response = self.llm.chat(
                [{"role": "user", "content": f"从任务描述提取简洁英文项目名（用下划线连接），只返回名称。\n\n任务：{task}"}],
                temperature=0.3,
            )
            return response.strip().replace(" ", "_").replace("-", "_")
        except Exception:
            words = re.findall(r"\b[A-Z][a-z]+\b|\b[A-Z]+\b", task[:50])
            return "_".join(words[:3]) if words else "Untitled_Project"

    def _load_and_fill_templates(self, task, routing, project_name):
        """加载并填充模板"""
        spec_content = self._generate_spec_content(task, routing.task_type.value)

        # 填充 base_spec
        base_path = os.path.join(self.templates_dir, "base_spec.md")
        if os.path.exists(base_path):
            with open(base_path, "r", encoding="utf-8") as f:
                content = f.read()

            content = content.replace("{{Project_Name}}", project_name)
            content = content.replace("{{一句话描述核心交付物}}", task)
            content = content.replace("{{Step_ID}}", "stage_1")
            content = content.replace(
                "{{约束项 1}}",
                "\n".join(f"- {c}" for c in spec_content.get("must_constraints", ["待确认"])) or "- 待确认",
            )
            content = content.replace(
                "{{禁止项 1}}",
                "\n".join(f"- {c}" for c in spec_content.get("must_not_constraints", ["待确认"])) or "- 待确认",
            )

            artifacts = spec_content.get("artifacts", [])
            artifacts_table = "\n".join(
                f"| {a.get('name', '')} | {a.get('format', '')} | {a.get('acceptance_criteria', '')} |"
                for a in artifacts
            ) or "| 待确认 | 待确认 | 待确认 |"
            content = content.replace(
                "| {{Item_Name}} | {{Format}} | {{Condition}} |", artifacts_table
            )

            master_path = os.path.join(self.spec_workspace_dir, "master_spec.md")
            with open(master_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("master_spec.md 已创建")

    def _generate_spec_content(self, task, task_type):
        prompt = f"""为任务生成 Spec 配置。

任务: {task}
类型: {task_type}

返回 JSON:
{{
  "must_constraints": ["必须做的事"],
  "must_not_constraints": ["禁止做的事"],
  "artifacts": [{{"name": "交付物", "format": "格式", "acceptance_criteria": "验收标准"}}],
  "decisions": ["关键决策"]
}}

artifacts 必须是最终交付的文件，不是状态/进度文件。只返回 JSON。"""

        try:
            result = self.llm.structured_chat(
                [{"role": "user", "content": prompt}], TemplateSpecContent, temperature=0.5
            )
            return result.model_dump()
        except Exception as e:
            logger.warning(f"Spec 生成失败: {e}")
            return {"must_constraints": [], "must_not_constraints": [], "artifacts": [], "decisions": []}

    def _create_pipeline(self, task_type, task="") -> List[PipelineStage]:
        stages_data = PIPELINE_MAP.get(task_type.value, [])
        pipeline = []

        for i, sd in enumerate(stages_data):
            stage = PipelineStage(**sd)
            if i == 0:
                stage.status = "active"
            pipeline.append(stage)

            # 创建步骤文件
            desc = STAGE_DESC.get(sd["id"], "执行此阶段")
            content = STEP_TEMPLATE.format(
                name=sd["name"], id=sd["id"], desc=desc,
                criteria="- [ ] 标准 1\n- [ ] 标准 2\n- [ ] 标准 3",
                status=stage.status, time=datetime.now().isoformat(),
            )

            step_path = os.path.join(self.spec_workspace_dir, "steps", sd["file"])
            with open(step_path, "w", encoding="utf-8") as f:
                f.write(content)

        return pipeline

    def _create_manifest(self, project_name, pipeline) -> Manifest:
        current = next((s.id for s in pipeline if s.status == "active"), "")
        manifest = Manifest(
            project_name=project_name, status="active",
            current_stage=current, pipeline=pipeline,
        )
        with open(os.path.join(self.spec_workspace_dir, "manifest.json"), "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))
        return manifest
