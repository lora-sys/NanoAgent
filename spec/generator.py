"""
Spec 生成器 - NanoAgent
负责根据用户任务生成高质量 Spec（使用模板系统）
"""

from loguru import logger
from spec.models import TaskSpec, SpecContent


class SpecGenerator:
    """Spec 生成器 - 使用模板系统和 LLM 生成 Spec"""

    def __init__(self, llm_client):
        """
        初始化 Spec 生成器

        Args:
            llm_client: LLM 客户端实例
        """
        self.llm = llm_client

    def generate_spec(self, task: str) -> TaskSpec:
        """
        根据用户任务生成高质量 Spec（使用模板系统）

        Args:
            task: 用户任务描述

        Returns:
            生成的 TaskSpec 对象
        """
        from identity.soul_loader import load_soul
        from identity.template_loader import load_template, fill_template

        # 步骤 1: 用 LLM 生成 task_type 和核心字段值
        soul_content = load_soul()

        prompt = f"""为以下任务生成 Spec 配置。

任务: {task}
Agent 设定: {soul_content}

返回 JSON:
{{
  "task_type": "chat/code/writing/analyze",
  "overall_goal": "核心目标",
  "success_criteria": ["可验证标准 1", "标准 2"],
  "current_progress": "当前阶段描述",
  "completed_steps": [],
  "remaining": ["待做事项 1", "待做事项 2"],
  "always": ["必须遵守的规则"],
  "ask_first": ["需确认的事项"],
  "never": ["禁止的操作"],
  "self_check_instructions": ["自查要点"],
  "process_requirements": ["流程要求"]
}}

要求:
- success_criteria 必须具体、可验证
- always/never 是行为约束
- 只返回 JSON
"""

        messages = [
            {"role": "system", "content": "Spec 生成器，只输出 JSON。"},
            {"role": "user", "content": prompt},
        ]

        spec_content: SpecContent = self.llm.structured_chat(
            messages, SpecContent, temperature=0.3
        )

        # 步骤 2: 根据 task_type 加载对应的模板
        template = load_template(spec_content.task_type)
        if template is None:
            logger.warning(
                f"Template not found for task_type: {spec_content.task_type}, using base template"
            )
            template = load_template("base")
            if template is None:
                logger.warning(
                    "No template available, creating spec directly from content"
                )
                # 如果没有模板，直接从内容创建 TaskSpec
                return TaskSpec(
                    task_type=spec_content.task_type,
                    overall_goal=spec_content.overall_goal,
                    success_criteria=spec_content.success_criteria,
                    progress_tracking={
                        "current_progress": spec_content.current_progress,
                        "completed_steps": spec_content.completed_steps,
                        "remaining": spec_content.remaining,
                    },
                    process_requirements=spec_content.process_requirements,
                    boundaries={
                        "always": spec_content.always,
                        "ask_first": spec_content.ask_first,
                        "never": spec_content.never,
                    },
                    self_check_instructions=spec_content.self_check_instructions,
                    human_in_loop_points=[],
                    additional_notes="",
                )

        # 步骤 3: 用 LLM 生成的值填充模板占位符
        filled_template = fill_template(
            template,
            overall_goal=spec_content.overall_goal,
            task_type=spec_content.task_type,
            success_criteria="\n".join(f"- {c}" for c in spec_content.success_criteria),
            current_progress=spec_content.current_progress,
            completed_steps="\n".join(f"- {s}" for s in spec_content.completed_steps),
            remaining_steps="\n".join(f"- {s}" for s in spec_content.remaining),
            always="\n".join(f"- {a}" for a in spec_content.always),
            ask_first="\n".join(f"- {a}" for a in spec_content.ask_first),
            never="\n".join(f"- {n}" for n in spec_content.never),
            self_check_instructions="\n".join(
                f"- {i}" for i in spec_content.self_check_instructions
            ),
        )

        # 步骤 4: 将填充后的模板内容转换为 TaskSpec 对象
        spec = TaskSpec(
            task_type=spec_content.task_type,
            overall_goal=spec_content.overall_goal,
            success_criteria=spec_content.success_criteria,
            progress_tracking={
                "current_progress": spec_content.current_progress,
                "completed_steps": spec_content.completed_steps,
                "remaining": spec_content.remaining,
            },
            process_requirements=spec_content.process_requirements,
            boundaries={
                "always": spec_content.always,
                "ask_first": spec_content.ask_first,
                "never": spec_content.never,
            },
            self_check_instructions=spec_content.self_check_instructions,
            human_in_loop_points=[],
            additional_notes=filled_template,  # 将填充后的模板保存在 additional_notes 中
        )

        logger.info(
            "Spec generated with template",
            task_type=spec.task_type,
            goal=spec.overall_goal,
            template_used=template is not None,
        )
        return spec
