"""
工具模块 - 支持动态加载的技能式架构

架构特点：
1. 类别索引：简洁描述，始终加载，节省 Token
2. 按需加载：工具详情仅在需要时加载
3. 模块化：按功能分组（file/, hitl/ 等）
4. 延迟导入：节省内存和启动时间
"""

from .registry import ToolRegistry, get_tool_registry, get_available_tools, CATEGORIES

__all__ = ["ToolRegistry", "get_tool_registry", "get_available_tools", "CATEGORIES"]
