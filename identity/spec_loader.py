from pathlib import Path
from loguru import logger
from core.tools.file import safe_read_file, safe_write_file

class SpecLoader:
    def __init__(self, specs_dir: str = "specs"):
        self.specs_dir = Path(specs_dir)

    def detect_task_type(self, task: str) -> str:
        task_lower = task.lower()
        if any(k in task_lower for k in ["code", "写代码", "implement", "function", "class", "debug"]):
            return "code"
        elif any(k in task_lower for k in ["write", "写作", "report", "文章"]):
            return "writing"
        elif any(k in task_lower for k in ["analyze", "分析", "data", "计算"]):
            return "analyze"
        return "chat"

    def load_and_fill_spec(self, task: str) -> str:
        """加载模板并填入当前任务信息"""
        task_type = self.detect_task_type(task)
        template_path = self.specs_dir / f"{task_type}.md"
        
        if not template_path.exists():
            template_path = self.specs_dir / "base.md"

        # 读取模板
        template = safe_read_file(str(template_path.relative_to("."))) if template_path.exists() else "# Default Spec"

        # 简单填入
        filled = template.replace("{overall_goal}", task)
        filled = filled.replace("{task_type}", task_type)

        # 写入临时文件（记录用）
        safe_write_file(f"current_spec_{task_type}.md", filled)

        logger.info(f"Loaded Spec for type: {task_type}")
        return filled