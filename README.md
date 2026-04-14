# NanoAgent

> **Nano** = Minimal dependencies + Clear layers. Delivery-first, zero-magic, async-native.

## 快速开始

```bash
# 运行默认任务
uv run main.py

# 运行自定义任务
uv run main.py "帮我写一个 Python 快速排序实现"
```

## 架构

```
nanoagent/
├── core/              # 核心：Agent 回路 + 执行器
├── domain/            # 领域层：模型 + 规则引擎 + 异常
├── infrastructure/    # 基础设施：LLM + 配置 + 缓存 + 工具
├── application/       # 应用层：路由 + Manifest + Spec 初始化
├── presentation/      # 展示层：CLI 界面
├── identity/          # 身份：soul.md + 模板加载
├── spec/              # Spec 生成器 + 上下文
├── templates/         # 任务模板 (.md)
└── agent_workspace/   # Agent 工作目录
```

## 技术栈

| 用途 | 技术 |
|------|------|
| Schema & State | `pydantic` |
| LLM 调用 | `litellm` |
| 日志 | `loguru` |
| 包管理 | `uv` |
| 模板 | `.md` + 占位符替换 |

## 核心设计

- **ReAct 循环**: Think → Act → Observe → Reflection
- **Manifest 驱动**: 多阶段流水线，阶段推进 + 回溯回填
- **人类介入**: 审批 / 干预 / 反馈 / 升级 4 种 HITL 工具
- **沙箱文件**: 所有文件操作限制在 `agent_workspace/` 内
- **配置集中**: `nanoagent.toml` + `config/*.toml`

## 配置

编辑 `nanoagent.toml` 配置 LLM 模型、Mock 模式、最大步数等：

```toml
[llm.default]
model = "openai/gpt-4o"
mock = false
```

## 规范

详细架构规范见 [AGENT.md](AGENT.md)
