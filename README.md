# NanoAgent

极简 Agent 框架 - 零魔法，高性能

## 特性

- **极简设计**：核心逻辑不到 200 行代码
- **零魔法**：纯 Python 内置函数，无复杂依赖
- **高性能**：使用 Python 内置函数，最小化开销
- **易扩展**：简单的工具注册机制
- **灵活控制**：无步数限制，自定义停止条件

## 快速开始

```bash
# 执行任务
uv run main.py run "帮我读取 README.md"

# 限制迭代次数
uv run main.py run "帮我读取 README.md" --max 5

# 交互式对话
uv run main.py chat
```

## 核心架构

```
NanoAgent
├── LLM 客户端    # 统一的 LLM 接口
├── 工具注册表    # 简单的工具管理
├── 任务跟踪      # 轻量级 spec 系统
└── 主循环        # 简单的 LLM + 工具箱循环
```

## 工具系统

内置工具：
- `read_file` - 读取文件
- `list_files` - 列出目录
- `edit_file` - 编辑文件
- `run_bash` - 执行命令

自定义工具：
```python
from core.agent import NanoAgent

agent = NanoAgent()

# 注册自定义工具
agent.tools.register("my_tool", my_function, "工具描述")
```

## 配置

编辑 `nanoagent.toml`：

```toml
[llm]
model = "openai/gpt-4o"
temperature = 0.7
max_tokens = 4096

[llm.mock]
enabled = true
mode = "random"
responses_file = "tests/fixtures/llm_mock_simple.json"
```

## 设计原则

1. **简单优先**：能用内置函数的，不用第三方库
2. **零魔法**：所有逻辑都是显式的
3. **高性能**：最小化依赖和开销
4. **易理解**：代码即文档