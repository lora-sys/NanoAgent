"""
Spec 初始化器 - NanoAgent
负责创建 Spec 结构、生成 manifest 和初始化步骤
基于原始 templates/manifest.json 格式
"""

import os
from typing import Dict, List
from datetime import datetime
from spec.models import PipelineStage, Manifest, TemplateSpecContent
from .llm_client import NanoLLMClient


class SpecInitializer:
    """Spec 初始化器"""

    def __init__(
        self, base_dir: str = None, model: str = "openai/qwen3.5-plus", llm_client=None
    ):
        self.base_dir = base_dir or os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
        self.templates_dir = os.path.join(self.base_dir, "templates", "moubles")
        self.spec_workspace_dir = os.path.join(self.base_dir, ".spec")
        # 使用传入的 llm_client，如果没有则创建新的
        self.llm = llm_client if llm_client else NanoLLMClient(model)

    def init_spec(self, task: str, routing_decision) -> Manifest:
        """
        初始化 Spec

        Args:
            task: 用户任务描述
            routing_decision: 路由决策结果

        Returns:
            Manifest: 生成的 manifest 对象
        """
        print(f"\n{'=' * 60}")
        print("🚀 初始化 Spec 系统")
        print(f"{'=' * 60}\n")

        # 1. 创建目录结构
        self._create_spec_structure()

        # 2. 生成项目名称
        project_name = self._generate_project_name(task)

        # 3. 加载并填充模板
        self._load_and_fill_templates(
            task, routing_decision, routing_decision.template_modules, project_name
        )

        # 4. 创建步骤文件
        pipeline = self._create_pipeline(routing_decision.task_type, task)

        # 5. 生成 manifest.json
        manifest = self._create_manifest(project_name, pipeline)

        print("\n✅ Spec 初始化完成！")
        print(f"📁 Spec 目录: {self.spec_workspace_dir}")
        print(f"📋 当前阶段: {manifest.current_stage}")
        print(f"📊 总步骤数: {len(manifest.pipeline)}\n")

        return manifest

    def _create_spec_structure(self):
        """创建 Spec 目录结构"""
        print("📂 创建目录结构...")

        directories = [
            self.spec_workspace_dir,
            os.path.join(self.spec_workspace_dir, "steps"),
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"  ✓ {directory}")

    def _generate_project_name(self, task: str) -> str:
        """使用 LLM 生成项目名称"""
        prompt = f"""从以下任务描述中提取项目名称：

任务：{task}

要求：
1. 项目名称应该简洁、有意义
2. 使用英文，单词首字母大写（如：GreenEnergy、FastAPI_User_Login）
3. 只返回项目名称，不要其他内容

请直接返回项目名称："""

        try:
            response = self.llm.chat(
                [{"role": "user", "content": prompt}], temperature=0.3
            )
            project_name = response.strip().replace(" ", "_").replace("-", "_")
            print(f"  ✓ LLM 生成项目名称: {project_name}")
            return project_name
        except Exception as e:
            print(f"  ⚠️ LLM 生成失败，使用回退方案: {e}")
            # 回退方案：使用简单的关键词提取
            import re

            words = re.findall(r"\b[A-Z][a-z]+\b|\b[A-Z]+\b", task[:50])
            if words:
                return "_".join(words[:3])
            return "Untitled_Project"

    def _generate_spec_content(self, task: str, task_type: str) -> Dict:
        """使用 LLM 生成 Spec 内容（填充占位符）"""
        prompt = f"""为以下任务生成详细的 Spec 内容：

任务：{task}
任务类型：{task_type}

请生成以下内容（JSON 格式）：

{{
  "must_constraints": [
    "约束 1：具体要求",
    "约束 2：具体要求"
  ],
  "must_not_constraints": [
    "禁止项 1",
    "禁止项 2"
  ],
  "artifacts": [
    {{
      "name": "交付物名称",
      "format": "格式",
      "acceptance_criteria": "验收标准"
    }}
  ],
  "decisions": [
    "关键决策点 1",
    "关键决策点 2"
  ]
}}

要求：
- must_constraints: 必须包含的具体约束
- must_not_constraints: 绝对禁止的事项
- artifacts: 交付物清单，包含名称、格式、验收标准
- decisions: 已确定的关键决策（初始阶段可以留空）

只返回合法的 JSON，不要其他内容。"""

        try:
            spec_content = self.llm.structured_chat(
                [{"role": "user", "content": prompt}],
                TemplateSpecContent,
                temperature=0.5,
            )
            print(f"  ✓ LLM 生成 Spec 内容: {len(spec_content.artifacts)} 个交付物")
            return spec_content.model_dump()
        except Exception as e:
            print(f"  ⚠️ LLM 生成 Spec 内容失败: {e}")
            return {
                "must_constraints": ["确保符合项目规范"],
                "must_not_constraints": ["违反安全原则"],
                "artifacts": [],
                "decisions": [],
            }

    def _load_and_fill_templates(
        self,
        task: str,
        routing_decision,
        template_modules: List[str] = None,
        project_name: str = None,
    ):
        """加载并填充模板（使用 LLM 生成内容）"""
        print("\n📄 加载并填充模板...")

        # 生成 Spec 内容
        spec_content = self._generate_spec_content(
            task, routing_decision.task_type.value
        )

        # 加载 base_spec.md
        base_template_path = os.path.join(self.templates_dir, "base_spec.md")
        if os.path.exists(base_template_path):
            with open(base_template_path, "r", encoding="utf-8") as f:
                base_template = f.read()

            # 填充基本占位符
            content = base_template.replace(
                "{{Project_Name}}",
                project_name if project_name else self._generate_project_name(task),
            )
            content = content.replace("{{一句话描述核心交付物}}", task)
            content = content.replace("{{Step_ID}}", "stage_1")

            # 填充 MUST 约束
            must_list = "\n".join(
                [f"- {c}" for c in spec_content.get("must_constraints", [])]
            )
            content = content.replace(
                "{{约束项 1}}", must_list if must_list else "- 待确认"
            )

            # 填充 MUST NOT 约束
            must_not_list = "\n".join(
                [f"- {c}" for c in spec_content.get("must_not_constraints", [])]
            )
            content = content.replace(
                "{{禁止项 1}}", must_not_list if must_not_list else "- 待确认"
            )

            # 填充交付物清单
            artifacts_table = ""
            for artifact in spec_content.get("artifacts", []):
                artifacts_table += f"| {artifact.get('name', '')} | {artifact.get('format', '')} | {artifact.get('acceptance_criteria', '')} |\n"

            if not artifacts_table:
                artifacts_table = "| 待确认 | 待确认 | 待确认 |\n"

            content = content.replace(
                "| {{Item_Name}} | {{Format}} | {{Condition}} |", artifacts_table
            )

            # 填充决策点
            decisions_section = "\n".join(
                [f"- \\[DECISION\\]: {d}" for d in spec_content.get("decisions", [])]
            )
            content = content.replace(
                "- \\[DECISION\\]: {{记录点}}",
                decisions_section if decisions_section else "- \\[DECISION\\]: 待记录",
            )

            # 保存到 .spec/master_spec.md
            master_spec_path = os.path.join(self.spec_workspace_dir, "master_spec.md")
            with open(master_spec_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("  ✓ 创建: master_spec.md")

        # 使用 routing_decision.template_modules 或指定的 template_modules
        if template_modules is None:
            template_modules = routing_decision.template_modules

        # 加载其他模板
        for template_name in template_modules:
            template_path = os.path.join(self.templates_dir, template_name)
            if os.path.exists(template_path):
                print(f"  ✓ 参考: {template_name}")

    def _get_task_type_templates(self, task_type) -> List[str]:
        """根据任务类型获取模板列表"""
        templates_map = {
            "code": ["code_logic.md", "code_api.md", "code_db.md", "project_plan.md"],
            "writing": ["writing_core.md"],
            "analyze": ["analyze_research.md"],
            "chat": ["chat_consultancy.md"],
        }
        return templates_map.get(task_type.value, [])

    def _create_pipeline(self, task_type, task: str = "") -> List[PipelineStage]:
        """创建 pipeline"""
        print("\n📋 创建 pipeline...")

        # 根据任务类型定义 pipeline
        pipeline_map = {
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

        stages_data = pipeline_map.get(task_type.value, [])
        pipeline = []

        for i, stage_data in enumerate(stages_data):
            # 创建 PipelineStage 对象
            stage = PipelineStage(**stage_data)

            # 设置第一个阶段为 active
            if i == 0:
                stage.status = "active"

            pipeline.append(stage)

            # 创建步骤文件（传递 task 参数）
            step_file = os.path.join(
                self.spec_workspace_dir, "steps", stage_data["file"]
            )
            with open(step_file, "w", encoding="utf-8") as f:
                f.write(self._generate_step_content(stage, task))
            print(f"  ✓ 创建: steps/{stage_data['file']}")

        return pipeline

    def _generate_step_content(self, stage: PipelineStage, task: str = "") -> str:
        """使用 LLM 动态生成步骤文件内容"""
        if not task:
            # 回退到通用模板
            return f"""# {stage.name}

## 阶段 ID
{stage.id}

## 描述
{self._get_stage_description(stage.id)}

## 成功标准
- [ ] 标准 1
- [ ] 标准 2
- [ ] 标准 3

## 边界约束
### Always (必须做)
- 确保符合项目规范
- 遵循最佳实践

### Ask First (先询问)
- 重大技术决策
- 范围变更

### Never (绝对禁止)
- 违反安全原则
- 硬编码敏感信息

## 交互提示
{self._get_interaction_prompt(stage.id)}

---

**状态**: {stage.status}
**创建时间**: {datetime.now().isoformat()}
"""

        # 使用 LLM 生成具体内容
        prompt = f"""为阶段 {stage.name} 生成具体的约束和成功标准：

任务：{task}
阶段：{stage.name}
阶段 ID：{stage.id}

请生成以下内容：

1. **成功标准**（3-5 条具体的、可验证的标准）
2. **边界约束**：
   - Always（必须做）：3-5 条
   - Ask First（先询问）：2-3 条
   - Never（绝对禁止）：2-3 条
3. **交互提示**：该阶段需要询问用户什么信息

请以以下格式返回（注意：不要包含"边界约束："标签，直接使用 Markdown 标题）：

成功标准：
- [ ] 标准 1
- [ ] 标准 2
...

### Always (必须做)
- 约束 1
- 约束 2
...

### Ask First (先询问)
- 询问 1
- 询问 2
...

### Never (绝对禁止)
- 禁止 1
- 禁止 2
...

交互提示：
提示内容

请只返回上述内容，不要其他说明。"""

        try:
            response = self.llm.chat(
                [{"role": "user", "content": prompt}], temperature=0.5
            )
            print(f"  ✓ LLM 生成步骤内容: {stage.name}")

            return f"""# {stage.name}

## 阶段 ID
{stage.id}

## 描述
{self._get_stage_description(stage.id)}

## 成功标准
{response}

---

**状态**: {stage.status}
**创建时间**: {datetime.now().isoformat()}
"""
        except Exception as e:
            print(f"  ⚠️ LLM 生成步骤内容失败: {e}")
            # 回退到通用模板
            return f"""# {stage.name}

## 阶段 ID
{stage.id}

## 描述
{self._get_stage_description(stage.id)}

## 成功标准
- [ ] 标准 1
- [ ] 标准 2
- [ ] 标准 3

## 边界约束
### Always (必须做)
- 确保符合项目规范
- 遵循最佳实践

### Ask First (先询问)
- 重大技术决策
- 范围变更

### Never (绝对禁止)
- 违反安全原则
- 硬编码敏感信息

## 交互提示
{self._get_interaction_prompt(stage.id)}

---

**状态**: {stage.status}
**创建时间**: {datetime.now().isoformat()}
"""

    def _get_stage_description(self, stage_id: str) -> str:
        """获取阶段描述"""
        descriptions = {
            "stage_1": "明确需求和目标",
            "stage_2": "设计和规划",
            "stage_3": "实现和执行",
            "stage_4": "测试和验证",
            "stage_5": "部署和交付",
        }
        return descriptions.get(stage_id, "执行此阶段")

    def _get_interaction_prompt(self, stage_id: str) -> str:
        """获取交互提示"""
        prompts = {
            "stage_1": "请明确需求和目标。",
            "stage_2": "请进行设计和规划。",
            "stage_3": "请实现和执行。",
            "stage_4": "请进行测试和验证。",
            "stage_5": "请进行部署和交付。",
        }
        return prompts.get(stage_id, "请执行此阶段。")

    def _create_manifest(
        self, project_name: str, pipeline: List[PipelineStage]
    ) -> Manifest:
        """创建 manifest.json"""
        print("\n📊 生成 manifest.json...")

        # 获取当前阶段
        current_stage = ""
        for stage in pipeline:
            if stage.status == "active":
                current_stage = stage.id
                break

        # 创建 manifest
        manifest = Manifest(
            project_name=project_name,
            status="active",
            current_stage=current_stage,
            pipeline=pipeline,
        )

        # 保存 manifest
        manifest_path = os.path.join(self.spec_workspace_dir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

        print(f"  ✓ 创建: {manifest_path}")

        return manifest


# 使用示例
if __name__ == "__main__":
    from .router import RoutingDecision, TaskType

    initializer = SpecInitializer()

    # 模拟路由决策
    routing_decision = RoutingDecision(
        task_type=TaskType.CODE,
        confidence=0.95,
        template_modules=["base_spec", "code_logic", "code_api", "project_plan"],
        reasoning="规则路由匹配：检测到关键词和模式",
    )

    # 初始化 Spec
    manifest = initializer.init_spec(
        task="开发一个 FastAPI 用户登录模块", routing_decision=routing_decision
    )

    print(f"\n{'=' * 60}")
    print("📋 Manifest 预览")
    print(f"{'=' * 60}")
    print(manifest.model_dump_json(indent=2))
