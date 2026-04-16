# 工具使用测试报告

## 测试执行情况

### 测试环境
- 框架: nanoagent
- 测试时间: 2026-04-16
- LLM: 真实 LLM (通过 LiteLLM)
- 测试类型: 工具使用能力测试

### 测试结果

#### 基础功能测试 (3/10 通过)

| 测试 | 状态 | 使用的工具 | 预期工具 | 结果 |
|------|------|------------|----------|------|
| 读取文件 | ❌ | [] | ["read_file"] | 失败 |
| 列出文件 | ❌ | [] | ["list_files"] | 失败 |
| 运行命令 | ❌ | [] | ["run_bash"] | 失败 |

#### 完整功能测试 (0/10 通过)

所有 10 个测试都显示：
- 状态: failed
- 使用的工具: []
- 迭代次数: 1

## 问题分析

### 1. 工具定义不匹配 ❌

**问题描述:**
系统提示中的工具示例与实际工具定义不匹配。

**示例:**
```python
# 系统提示中的示例
<tool name="read_file" args='{"filename": "README.md"}'/>

# 实际工具定义
def read_file(filename: str) -> Dict[str, Any]:
    """Gets the full content of a file."""
```

**问题:**
- 系统提示使用 `filename` 参数
- 但工具实际定义使用 `path` 参数
- 导致模型无法正确调用工具

### 2. 工具描述不够明确 ❌

**问题描述:**
工具描述过于简单，缺乏使用示例和边界情况说明。

**示例:**
```python
def read_file(filename: str) -> Dict[str, Any]:
    """Gets the full content of a file."""
```

**改进建议:**
```python
def read_file(filename: str) -> Dict[str, Any]:
    """
    读取文件的完整内容
    
    Args:
        filename: 文件路径（相对或绝对路径）
        
    Returns:
        包含文件内容和路径的字典
        
    Example:
        read_file("README.md") -> {"file_path": "/path/README.md", "content": "..."}
        
    Notes:
        - 支持相对路径和绝对路径
        - 相对路径相对于当前工作目录
        - 如果文件不存在，返回错误信息
    """
```

### 3. 参数映射问题 ❌

**问题描述:**
工具注册表中的参数映射不够完善。

**当前映射:**
```python
param_mappings = {
    "read_file": {"path": "filename", "absolute_path": "filename"},
}
```

**问题:**
- 只处理了 `read_file` 的映射
- 其他工具没有参数映射
- 导致模型使用错误参数名时无法正确调用

### 4. 系统提示不够详细 ❌

**问题描述:**
系统提示缺少具体的使用指导和错误处理说明。

**当前问题:**
- 没有明确的工具使用流程
- 缺少错误处理指导
- 没有参数格式说明

## 改进建议

### 1. 统一工具参数命名 ✅

**建议:**
```python
# 统一使用 path 参数
def read_file(path: str) -> Dict[str, Any]:
    """读取文件内容"""
    pass

def list_files(path: str = ".") -> Dict[str, Any]:
    """列出目录文件"""
    pass

def edit_file(path: str, old_str: str, new_str: str) -> Dict[str, Any]:
    """编辑文件"""
    pass
```

### 2. 增强工具描述 ✅

**建议:**
```python
def read_file(path: str) -> Dict[str, Any]:
    """
    读取文件的完整内容
    
    使用场景:
    - 查看配置文件
    - 读取代码文件
    - 检查文档内容
    
    Args:
        path: 文件路径，支持相对路径和绝对路径
              相对路径相对于当前工作目录
    
    Returns:
        Dict: {
            "file_path": str,  # 文件的绝对路径
            "content": str     # 文件内容
        }
    
    Examples:
        read_file("README.md") -> 读取当前目录的 README.md
        read_file("/etc/hosts") -> 读取系统 hosts 文件
    
    Error Handling:
        - 如果文件不存在，返回错误信息
        - 如果没有读取权限，返回错误信息
    """
```

### 3. 改进系统提示 ✅

**建议:**
```
你是一个通用智能助手，帮助用户完成各种任务。

## 工具使用指南

### 何时使用工具
1. 用户明确要求读取文件、列出目录、运行命令时
2. 需要获取项目信息、代码内容时
3. 需要执行系统操作时

### 工具调用格式
<tool name="工具名" args='{"参数名": "参数值"}'/>

### 重要规则
1. **必须使用工具**: 当用户询问文件、目录、代码等信息时，必须先使用工具获取
2. **不要猜测**: 不要凭空猜测文件内容或目录结构
3. **参数格式**: JSON 参数必须使用单引号包裹，内部使用双引号
4. **路径处理**: 支持相对路径和绝对路径，相对路径相对于当前工作目录
5. **错误处理**: 如果工具返回错误，使用 <error> 标记描述问题

### 工具列表

#### read_file
- **用途**: 读取文件内容
- **参数**: path (文件路径)
- **示例**: <tool name="read_file" args='{"path": "README.md"}'/>

#### list_files  
- **用途**: 列出目录文件
- **参数**: path (目录路径，默认为当前目录)
- **示例**: <tool name="list_files" args='{"path": "."}'/>

#### edit_file
- **用途**: 编辑文件内容
- **参数**: path, old_str, new_str
- **示例**: <tool name="edit_file" args='{"path": "test.txt", "old_str": "hello", "new_str": "world"}'/>

#### run_bash
- **用途**: 执行系统命令
- **参数**: command (命令字符串)
- **示例**: <tool name="run_bash" args='{"command": "ls -la"}'/>

### 响应格式
- 正常响应: <response>你的回复内容</response>
- 错误响应: <error>错误描述</error>
```

### 4. 添加参数验证 ✅

**建议:**
```python
def _validate_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
    """验证参数是否正确"""
    tool = self._tools.get(tool_name)
    if not tool:
        return False
    
    schema = tool["schema"]
    required = schema.get("required", [])
    
    # 检查必需参数
    for param in required:
        if param not in arguments:
            return False
    
    return True
```

### 5. 改进错误处理 ✅

**建议:**
```python
def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
    """执行工具，增强错误处理"""
    tool = self._tools.get(name)
    if not tool:
        return {
            "error": f"Tool not found: {name}",
            "available_tools": list(self._tools.keys())
        }
    
    # 验证参数
    if not self._validate_arguments(name, arguments):
        return {
            "error": f"Invalid arguments for {name}",
            "expected_schema": tool["schema"]
        }
    
    try:
        return tool["function"](**self._map_arguments(name, arguments))
    except Exception as e:
        return {
            "error": f"Tool execution failed: {str(e)}",
            "tool": name,
            "arguments": arguments
        }
```

## 测试结论

### 当前状态
- ❌ 工具使用功能不正常
- ❌ 模型无法正确调用工具
- ❌ 参数映射存在问题
- ❌ 系统提示需要改进

### 改进优先级
1. **高优先级**: 修复工具参数命名不匹配
2. **高优先级**: 改进系统提示
3. **中优先级**: 增强工具描述
4. **中优先级**: 添加参数验证
5. **低优先级**: 改进错误处理

### 下一步行动
1. 修复工具参数命名问题
2. 重写系统提示
3. 增强工具描述
4. 添加参数验证
5. 重新测试工具使用功能

## 总结

当前框架的工具使用功能存在严重问题，需要立即修复。主要问题是工具定义与系统提示不匹配，导致模型无法正确使用工具。

建议按照上述改进优先级逐步修复问题，然后重新进行测试验证。
