"""
模板加载器 - 根据 task_type 加载对应的 Spec 模板
"""
import os
import re
from typing import Optional


def load_template(task_type: str) -> Optional[str]:
    """
    根据 task_type 加载对应的模板文件

    Args:
        task_type: 任务类型 (chat/code/writing/analyze)

    Returns:
        模板内容字符串，如果文件不存在则返回 None
    """
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'specs')
    template_file = os.path.join(template_dir, f'{task_type}.md')

    if not os.path.exists(template_file):
        # 如果特定类型的模板不存在，尝试使用 base.md
        base_template = os.path.join(template_dir, 'base.md')
        if os.path.exists(base_template):
            with open(base_template, 'r', encoding='utf-8') as f:
                template = f.read()
            # 应用相同的占位符规范化
            template = re.sub(r'\{\s+(\w+)\s+\}', r'{\1}', template)
            return template
        return None

    with open(template_file, 'r', encoding='utf-8') as f:
        template = f.read()

    # 标准化占位符：移除占位符内部的多余空格
    # 例如：{ success_criteria } -> {success_criteria}
    template = re.sub(r'\{\s+(\w+)\s+\}', r'{\1}', template)

    return template


def fill_template(template: str, **kwargs) -> str:
    """
    用 LLM 生成的值填充模板占位符

    Args:
        template: 模板字符串
        **kwargs: 占位符的值

    Returns:
        填充后的模板
    """
    # 简单的字符串替换
    result = template
    for key, value in kwargs.items():
        placeholder = f'{{{key}}}'
        result = result.replace(placeholder, str(value))
    return result