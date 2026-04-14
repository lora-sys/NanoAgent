"""
工具注册表和动态加载器
"""

from loguru import logger
from typing import Dict, Any, Optional, List
import importlib

# 类别索引
CATEGORIES = {
    "file": "文件操作：read_file, write_file, list_directory",
    "hitl": "人机交互：ask_user_question",
    "bash": "Shell 执行：run_bash",
}

CATEGORY_MODULES = {
    "file": "infrastructure.tools.file",
    "hitl": "infrastructure.tools.hitl",
    "bash": "infrastructure.tools.bash_tool",
}


class ToolRegistry:
    """工具注册表"""

    def __init__(self, config: Dict[str, Any] = None):
        self._loaded_categories: set = set()
        self._tool_cache: Dict[str, Dict[str, Any]] = {}
        self.config = config or {}

    def _load_category(self, category: str) -> None:
        """动态加载工具类别"""
        if category in self._loaded_categories:
            return

        try:
            module = importlib.import_module(CATEGORY_MODULES.get(category, ""))

            tool_mappings = {
                "file": {
                    "safe_read_file": {"input": "ReadFileInput"},
                    "safe_write_file": {"input": "WriteFileInput"},
                    "safe_list_directory": {"input": "ListDirectoryInput"},
                },
                "hitl": {
                    "ask_user_question": {"input": "AskUserQuestionInput"},
                },
                "bash": {
                    "run_bash": {"input": "BashInput"},
                },
            }

            self._tool_cache[category] = {}
            mappings = tool_mappings.get(category, {})

            for func_name, meta in mappings.items():
                func = getattr(module, func_name, None)
                input_class = getattr(module, meta.get("input"), None)

                if func:
                    schema = input_class.model_json_schema() if input_class else {}
                    self._tool_cache[category][func_name] = {
                        "function": func,
                        "description": (func.__doc__ or "No description").strip(),
                        "schema": schema,
                        "category": category,
                    }

            self._loaded_categories.add(category)
            logger.info(f"Loaded category '{category}': {len(self._tool_cache[category])} tools")

        except Exception as e:
            logger.error(f"Error loading category {category}: {e}")

    def get_all_tools(self, category: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """获取所有工具"""
        if category:
            self._load_category(category)
            return self._tool_cache.get(category, {})

        for cat in CATEGORIES:
            self._load_category(cat)

        result = {}
        for cat_tools in self._tool_cache.values():
            result.update(cat_tools)
        return result

    def execute(self, name: str, arguments: Dict) -> Any:
        """执行工具"""
        tool = self.get_all_tools().get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")

        try:
            result = tool["function"](**arguments)
            logger.info(f"Executed {name}")
            return result
        except Exception as e:
            logger.error(f"Tool error {name}: {e}")
            return f"Error: {str(e)}"

    def get_tool_descriptions(self) -> str:
        """获取工具描述文本"""
        tools = self.get_all_tools()
        descriptions = []
        for name, t in tools.items():
            desc = f"- {name}: {t['description']}"
            # 添加参数信息
            schema = t.get('schema', {})
            properties = schema.get('properties', {})
            required = schema.get('required', [])
            
            if properties:
                params = []
                for param_name, param_info in properties.items():
                    param_type = param_info.get('type', 'string')
                    param_desc = param_info.get('description', '')
                    is_required = param_name in required
                    req_marker = " (必需)" if is_required else f" (默认: {param_info.get('default', '无')})"
                    params.append(f"  - {param_name}: {param_type}{req_marker} - {param_desc}")
                
                if params:
                    desc += "\n  参数:\n" + "\n".join(params)
            
            descriptions.append(desc)
        
        return "\n".join(descriptions)
