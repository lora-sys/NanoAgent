from pathlib import Path


def load_soul(soul_path: str = "soul.md") -> str:
    path = Path(soul_path)
    if not path.exists():
        raise FileNotFoundError(f"请先创建{soul_path}文件,定义Agent 的灵魂")
    return path.read_text(encoding="utf-8")
