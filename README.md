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
├── 提示链       # 复杂任务拆解
├── 路由器       # 智能任务分发
└── 主循环        # 简单的 LLM + 工具箱循环
```

## 工具系统

内置工具：
- `read_file` - 读取文件
- `list_files` - 列出目录
- `edit_file` - 编辑文件
- `run_bash` - 执行命令
- `grep` - ripgrep 搜索

## 测试

```bash
# 单元测试（mock 模式）
uv run pytest tests/agent/ -m unit -v

# 集成测试（real API）
uv run pytest tests/agent/ -m integration -v

# 全部测试
uv run pytest tests/agent/ -v
```

新增工具测试：`tests/agent/test_<tool>.py`，使用 `AgentTestHarness` 框架。

自定义工具：
```python
from core.agent import NanoAgent

agent = NanoAgent()

# 注册自定义工具
agent.tools.register("my_tool", my_function, "工具描述")
```

## 路由模块

智能路由器支持多种路由策略：

### 基本路由

```python
from core.router import Router

# 创建路由器
router = Router("my_router", default_target="general")

# 添加路由规则
router.add_route(
    name="数据库路由",
    target="database",
    condition="数据库",
    priority=1
).add_route(
    name="搜索路由",
    target="search",
    condition="搜索",
    priority=1
)

# 执行路由
decision = await router.route("查询数据库")
print(decision.target)  # "database"
```

### 智能路由（使用 LLM）

```python
from core.router import create_smart_router

# 创建智能路由器
router = create_smart_router()
router.set_llm_client(llm_client)

# 添加基本路由
router.add_route("数据库路由", "database", "数据库")

# 智能路由会自动处理复杂任务
decision = await router.route("分析销售数据趋势")
```

### 自定义路由函数

```python
def custom_condition(task: str) -> bool:
    return len(task) > 20

router.add_route(
    name="长任务路由",
    target="long",
    condition=custom_condition
)
```

### 路由特性

- **关键词路由**：快速匹配关键词
- **函数路由**：自定义路由逻辑
- **智能路由**：使用 LLM 进行复杂决策
- **优先级路由**：按优先级匹配
- **异步支持**：完整的异步 API
- **路由上下文**：跟踪路由历史和状态

## 提示链模块

用于处理复杂任务的链式执行：

### 基本使用

```python
from core.chain import PromptChain, ChainStep

# 创建提示链
chain = PromptChain([
    ChainStep("步骤1", "请执行第一个步骤"),
    ChainStep("步骤2", "请执行第二个步骤"),
    ChainStep("步骤3", "请执行第三个步骤"),
])

# 执行提示链
result = await chain.run("处理这个任务", llm_client)
```

### 预定义链

```python
from core.chain import create_analysis_chain

# 使用预定义的分析链
chain = create_analysis_chain()
result = await chain.run("分析项目代码结构", llm_client)
```

### 提示链特性

- **步骤化执行**：将复杂任务分解为多个步骤
- **上下文共享**：步骤之间共享上下文数据
- **错误处理**：支持错误恢复和继续执行
- **异步支持**：完整的异步 API
- **自定义处理器**：支持自定义步骤处理逻辑

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

## 示例

查看 `examples/` 目录中的示例：

- `async_demo.py` - 异步功能和流式响应
- `chain_demo.py` - 提示链基本使用
- `chain_real_world.py` - 提示链实际应用场景
- `router_demo.py` - 路由模块使用示例
- `sync_vs_async.py` - 同步 vs 异步对比

运行示例：
```bash
PYTHONPATH=. uv run python examples/router_demo.py
```

## 设计原则

1. **简单优先**：能用内置函数的，不用第三方库
2. **零魔法**：所有逻辑都是显式的
3. **高性能**：最小化依赖和开销
4. **易理解**：代码即文档
5. **单一职责**：每个模块专注于一个功能
6. **异步优先**：完整支持异步操作
7. **可测试性**：易于测试和验证
8. **零依赖**：最小化第三方依赖