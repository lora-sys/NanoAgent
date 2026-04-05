"""
工具注册表和动态加载器

实现类似 skills 模式的工具管理：
- 类别索引（始终加载，节省 Token）
- 工具详情（按需加载）
- 延迟导入（节省内存）
"""
from loguru import logger
from typing import Dict, Any, Optional
import importlib

# 第一层：类别索引（始终加载，简洁描述）
CATEGORIES = {
    "file": "文件操作：read_file, write_file, list_directory",
    "hitl": "人机交互：ask_user_question, present_decision_for_approval, monitor_agent, human_intervention, collect_human_feedback, escalate_to_human"
}

# 工具模块映射（按需导入）
CATEGORY_MODULES = {
    "file": "core.tools.file",
    "hitl": "core.tools.hitl"
}

class ToolRegistry:
    """工具注册表 - 支持动态加载"""
    
    def __init__(self):
        self._loaded_categories: set = set()
        self._tool_cache: Dict[str, Dict[str, Any]] = {}
    
    def get_categories(self) -> Dict[str, str]:
        """获取类别索引（始终加载，无额外开销）"""
        return CATEGORIES
    
    def _load_category(self, category: str) -> None:
        """动态加载工具类别"""
        if category in self._loaded_categories:
            return
        
        try:
            module_path = CATEGORY_MODULES.get(category)
            if not module_path:
                logger.warning(f"Unknown category: {category}")
                return
            
            # 动态导入模块
            module = importlib.import_module(module_path)
            
            # 扫描工具函数 - 使用预定义的工具映射
            tool_mappings = {
                "file": {
                    "safe_read_file": "ReadFileInput",
                    "safe_write_file": "WriteFileInput",
                    "safe_list_directory": "ListDirectoryInput"
                },
                "hitl": {
                    "ask_user_question": "AskUserQuestionInput",
                    "present_decision_for_approval": "PresentDecisionApprovalInput",
                    "monitor_agent": "MonitorInput",
                    "human_intervention": "InterveneInput",
                    "collect_human_feedback": "CollectFeedbackInput",
                    "escalate_to_human": "EscalateInput"
                }
            }
            
            self._tool_cache[category] = {}
            mappings = tool_mappings.get(category, {})
            
            for func_name, input_class_name in mappings.items():
                func = getattr(module, func_name, None)
                input_class = getattr(module, input_class_name, None)
                
                if func and input_class:
                    desc = func.__doc__ or input_class.__doc__ or "No description"
                    
                    self._tool_cache[category][func_name] = {
                        "function": func,
                        "description": desc.strip(),
                        "schema": input_class.model_json_schema(),
                        "category": category
                    }
            
            self._loaded_categories.add(category)
            logger.info(f"Loaded category '{category}' with {len(self._tool_cache[category])} tools")
            
        except Exception as e:
            logger.error(f"Error loading category {category}: {e}")
            import traceback
            traceback.print_exc()
    
    def get_tool(self, tool_name: str, category: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取工具详情（按需加载）"""
        # 如果指定了类别，只在该类别中查找
        if category:
            self._load_category(category)
            return self._tool_cache.get(category, {}).get(tool_name)
        
        # 否则在所有类别中查找
        for cat in CATEGORIES.keys():
            self._load_category(cat)
            tool = self._tool_cache.get(cat, {}).get(tool_name)
            if tool:
                return tool
        
        return None
    
    def get_all_tools(self, category: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """获取所有工具（可选按类别过滤）"""
        if category:
            self._load_category(category)
            return self._tool_cache.get(category, {})
        
        # 返回所有已加载的工具
        result = {}
        for cat in CATEGORIES.keys():
            self._load_category(cat)
            result.update(self._tool_cache.get(cat, {}))
        
        return result
    
    def get_tool_names(self, category: Optional[str] = None) -> list[str]:
        """获取工具名称列表"""
        tools = self.get_all_tools(category)
        return list(tools.keys())
    
    def execute(self, name: str, arguments: Dict) -> Any:
        """执行工具"""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        
        try:
            result = tool["function"](**arguments)
            logger.info(f"Executed tool {name}: {result[:100] if isinstance(result, str) else 'OK'}")
            return result
        except Exception as e:
            logger.error(f"Tool execution error {name}: {e}")
            return f"Error: {str(e)}"
    
    def get_tool_schemas(self) -> list:
        """获取工具的 OpenAI 格式 schema（所有可用工具）"""
        tools = self.get_all_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["schema"]
                }
            }
            for name, tool in tools.items()
        ]
    
    def get_tool_descriptions(self) -> str:
        """获取工具描述文本（类别索引 + 所有工具详情）"""
        # 第一层：类别索引
        category_desc = "\n".join(
            f"- {cat}: {desc}"
            for cat, desc in CATEGORIES.items()
        )
        
        # 第二层：所有工具的详情
        tool_details = []
        tools = self.get_all_tools()
        for name, tool in tools.items():
            desc = f"  • {name}: {tool['description']}"
            tool_details.append(desc)
        
        if tool_details:
            return f"工具类别：\n{category_desc}\n\n可用工具：\n" + "\n".join(tool_details)
        else:
            return f"工具类别：\n{category_desc}"


# 全局工具注册表实例
registry = ToolRegistry()

def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册表"""
    return registry


# 向后兼容的函数
def get_available_tools() -> Dict[str, Dict[str, Any]]:
    """获取所有可用工具（向后兼容）"""
    return registry.get_all_tools()