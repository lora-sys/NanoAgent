# 可组合模块功能说明

## 概述

可组合模块为 nanoagent 框架提供了灵活的功能拼装能力，允许用户根据需求自由组合不同的功能模块。

## 核心组件

### 1. 多模型接口 (`core/model_interface.py`)

提供统一的模型管理接口，支持模型注册、选择和切换。

**主要类：**
- `ModelTier` - 模型层级枚举（LIGHT, STANDARD, POWERFUL）
- `ModelInfo` - 模型信息数据类
- `BaseModelClient` - 基础模型客户端接口
- `ModelRegistry` - 模型注册表
- `ModelSelector` - 模型选择器

**使用示例：**
```python
from core.model_interface import get_global_registry, ModelInfo, ModelTier

# 获取全局注册表
registry = get_global_registry()

# 查询模型信息
info = registry.get_info("haiku")
print(f"模型: {info.name}, 层级: {info.tier}")
```

### 2. 可组合 Agent (`core/composable.py`)

提供灵活的 Agent 构建和执行能力。

**主要类：**
- `ComposableAgent` - 可组合的 Agent
- `AgentBuilder` - Agent 构建器（流式 API）

**使用示例：**
```python
from core import AgentBuilder, Router, PromptChain, ChainStep

# 使用构建器创建 Agent
agent = AgentBuilder() \
    .with_router(router) \
    .with_chain(chain) \
    .build()

# 执行任务
result = await agent.execute("任务描述", use_router=True, use_chain=True)
```

## 功能特性

### 1. 模块化设计

- 每个功能都是独立的模块
- 可以单独使用或组合使用
- 支持动态功能切换

### 2. 流式 API

- 使用链式调用构建 Agent
- 代码简洁易读
- 符合 Python 风格

### 3. 灵活配置

- 支持自定义路由器
- 支持自定义提示链
- 支持自定义模型选择

### 4. 异步支持

- 完整的异步 API
- 支持并发执行
- 提高性能

## 测试结果

使用 3 条提示词测试新功能：

### 测试 1：客户服务路由
```
提示词: "我要退款，订单号12345"
结果: ✅ 路由到 refund_service
验证: 路由功能正常
```

### 测试 2：文档创建链
```
提示词: "创建一个关于AI技术的文档"
结果: ✅ 执行路径: chaining
验证: 提示链功能正常
```

### 测试 3：完整功能拼装
```
提示词: "分析当前项目的架构设计"
结果: ✅ 执行路径: model_selection -> routing -> chaining
验证: 所有功能协同工作
```

## 使用场景

### 1. 客户服务系统
```python
# 创建客户服务路由器
router = Router("customer_service")
router.add_route("退款处理", "refund_service", "退款")
router.add_route("技术支持", "tech_support", "技术")

# 创建 Agent
agent = AgentBuilder().with_router(router).build()

# 处理客户请求
result = await agent.execute("我要退款", use_router=True)
```

### 2. 文档生成系统
```python
# 创建文档生成链
chain = PromptChain([
    ChainStep("提纲", "创建文档提纲"),
    ChainStep("内容", "撰写文档内容"),
    ChainStep("审核", "审核文档质量"),
])

# 创建 Agent
agent = AgentBuilder().with_chain(chain).build()

# 生成文档
result = await agent.execute("创建技术文档", use_chain=True)
```

### 3. 智能分析系统
```python
# 创建完整功能的 Agent
agent = AgentBuilder() \
    .with_router(router) \
    .with_chain(chain) \
    .with_model_registry(registry) \
    .build()

# 执行复杂分析
result = await agent.execute(
    "分析项目架构",
    use_router=True,
    use_chain=True,
    use_model_selection=True
)
```

## 设计原则

1. **零魔法** - 所有配置都是显式的
2. **模块化** - 每个功能都是独立的
3. **可组合** - 功能可以随意拼装
4. **异步优先** - 完整的异步支持
5. **易于测试** - 每个模块都可以独立测试

## 性能优化

- 按需加载功能模块
- 异步执行提高性能
- 智能模型选择降低成本
- 缓存机制减少重复计算

## 扩展性

框架支持轻松扩展：

1. 添加新的路由规则
2. 添加新的提示链步骤
3. 添加新的模型支持
4. 添加新的功能模块

## 总结

可组合模块为 nanoagent 框架提供了强大的灵活性，允许用户根据具体需求定制 Agent 的行为。通过模块化设计和流式 API，用户可以轻松构建复杂的 AI 应用。

主要优势：
- ✅ 灵活的功能组合
- ✅ 简洁的 API 设计
- ✅ 强大的扩展能力
- ✅ 完整的异步支持
- ✅ 符合框架设计原则
