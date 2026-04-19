"""ripgrep 内置搜索工具"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List


def grep(
    pattern: str,
    path: str = ".",
    context: int = 2,
    file_type: str = "",
    case_sensitive: bool = False,
    regex: bool = True,
    max_count: int = 100,
    include: str = "",
    exclude: str = "",
) -> Dict[str, Any]:
    """
    Searches for pattern in files using ripgrep (rg).

    Args:
        pattern: The search pattern (string or regex)
        path: Directory or file to search in (default: current directory)
        context: Number of context lines before/after match (default: 2)
        file_type: Filter by file type (e.g., "py", "js", "md")
        case_sensitive: Case sensitive search (default: False)
        regex: Treat pattern as regex (default: True)
        max_count: Maximum number of matches to return (default: 100)
        include: Include glob pattern (e.g., "*.py", "src/**/*.ts")
        exclude: Exclude glob pattern (e.g., "*.pyc", "node_modules")
    """
    if not pattern or not pattern.strip():
        return {"error": "Pattern cannot be empty", "matches": []}

    resolved_path = Path(path).resolve()

    cmd = ["rg", "--json", "--max-count", str(max_count), "--context", str(context)]

    if not regex:
        cmd.append("--fixed-strings")
    if case_sensitive:
        cmd.append("--case-sensitive")
    if file_type:
        cmd.extend(["--type", file_type])
    if include:
        cmd.extend(["--glob", include])
    if exclude:
        cmd.extend(["--glob", f"!{exclude}"])

    cmd.extend(["--", pattern, str(resolved_path)])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return {"error": "Search timeout (30s)", "matches": [], "path": str(resolved_path)}
    except FileNotFoundError:
        return {
            "error": "ripgrep (rg) not found. Install: brew install ripgrep | apt install ripgrep | cargo install ripgrep",
            "matches": [],
            "path": str(resolved_path),
        }
    except Exception as e:
        return {"error": str(e), "matches": [], "path": str(resolved_path)}

    matches: List[Dict[str, Any]] = []
    stats = {"files_with_matches": 0, "total_matches": 0}

    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        try:
            import json
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        if entry.get("type") == "match":
            match_data = entry.get("data", {})
            abs_path = match_data.get("path", {}).get("text", "")
            line_num = match_data.get("line_number", 0)
            content = match_data.get("lines", {}).get("text", "").rstrip("\n")

            matches.append({
                "file": abs_path,
                "line": line_num,
                "content": content,
            })

            stats["total_matches"] += 1
            if abs_path not in [m["file"] for m in matches[:-1]]:
                stats["files_with_matches"] += 1

    return {
        "matches": matches,
        "stats": stats,
        "path": str(resolved_path),
        "exit_code": result.returncode,
    }
