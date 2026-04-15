"""Jinja2 模板管理器"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader


class TemplateManager:
    def __init__(self, template_dir: str = "templates"):
        self.env = Environment(
            loader=FileSystemLoader(Path(template_dir)), autoescape=False
        )

    def render(self, name: str, **kwargs) -> str:
        try:
            return self.env.get_template(name).render(**kwargs)
        except Exception as e:
            return f"模板渲染失败: {e}"

    def get_system_prompt(self) -> str:
        return self.render("system.jinja2")

    def get_think_prompt(self, **kwargs) -> str:
        return self.render("think.jinja2", **kwargs)

    def get_planning_prompt(self, **kwargs) -> str:
        return self.render("planning.jinja2", **kwargs)

    def get_reflection_prompt(self, **kwargs) -> str:
        return self.render("reflection.jinja2", **kwargs)


_tm: TemplateManager = None


def get_template_manager() -> TemplateManager:
    global _tm
    if _tm is None:
        _tm = TemplateManager()
    return _tm
