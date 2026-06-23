# AGENTS.md

## 项目定位

本目录用于学习和练习 AI Agent 开发，主要使用 Python。示例应保持小而清晰，优先展示一个可独立运行的概念，例如对话、结构化输出、工具调用、记忆、规划或多 Agent 协作。

## 技术约定

- 默认使用 Python 3.11+。
- Python 代码遵循 PEP 8，优先添加类型标注。
- 每次生成或修改代码时，使用中文注释介绍代码用途和关键逻辑。
- 注释应简洁准确，重点说明模块职责、复杂流程、重要参数和设计原因；不要为显而易见的代码逐行添加冗余注释。
- 依赖保持精简；新增依赖时同步维护项目依赖文件。
- API Key 只能从环境变量读取，不得写入源码、日志或示例输出。
- DeepSeek API Key 的统一环境变量名为 `DEEPSEEK_API_KEY`。
- 示例代码应提供清晰的入口，优先使用 `main()` 和 `if __name__ == "__main__":`。
- 网络请求需要处理空响应、API 异常和 JSON 解析失败等常见错误。

## 模型与服务强制规则

本项目只允许实际调用 DeepSeek 官方模型和官方 API 服务。

- 默认模型：`deepseek-v4-flash`。
- 复杂推理或高质量任务：`deepseek-v4-pro`。
- 不得调用 OpenAI、Anthropic、Google、阿里云或其他厂商的模型服务。
- 不得使用第三方中转站、聚合平台或非官方兼容端点。
- 不得新增 `gpt-*`、`claude-*`、`gemini-*`、`qwen-*` 等非 DeepSeek 模型名。
- 不再新增 `deepseek-chat` 或 `deepseek-reasoner`；这两个旧模型名将于 2026-07-24 弃用。
- 修改旧示例时，应将旧模型名迁移为 `deepseek-v4-flash` 或 `deepseek-v4-pro`。

## API 调用规则

可以为了学习不同生态而使用 OpenAI SDK、Anthropic SDK、LangChain、LlamaIndex 或其他 Agent 框架，但最终请求必须按照 DeepSeek 官方文档改写并满足以下条件：

1. 请求发送到 DeepSeek 官方域名 `api.deepseek.com`。
2. 鉴权使用 `DEEPSEEK_API_KEY`。
3. `model` 必须显式设置为允许的 DeepSeek 模型。
4. 不得保留原 SDK 示例中的其他厂商端点、模型名或专属参数。
5. 优先采用 DeepSeek 官网展示的 OpenAI 兼容 Chat Completions 格式。

### 推荐的 Python 调用格式

```python
import os

from openai import OpenAI


client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
    stream=False,
)

print(response.choices[0].message.content)
```

### 使用 Anthropic SDK 时

只有在课程明确需要学习 Anthropic Messages API 时才保留 Anthropic SDK。此时也必须接入 DeepSeek 官方 Anthropic 兼容端点：

```python
import os

import anthropic


client = anthropic.Anthropic(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com/anthropic",
)

message = client.messages.create(
    model="deepseek-v4-flash",
    max_tokens=1024,
    system="You are a helpful assistant.",
    messages=[
        {"role": "user", "content": "Hello!"},
    ],
)

print(message.content)
```

## JSON 结构化输出

需要输出 JSON 时，使用 DeepSeek 官方 JSON Output 模式：

- 设置 `response_format={"type": "json_object"}`。
- system 或 user prompt 中必须明确包含 `json` 字样。
- prompt 中给出目标 JSON 结构示例，并明确必需字段和字段类型。
- 设置合理的 `max_tokens`，避免 JSON 被截断。
- 使用 `json.loads()` 解析响应，不要用字符串截取、正则表达式或 `eval()` 解析 JSON。
- 解析后应校验必需字段；对外输出时使用 `json.dumps()`。

```python
import json


response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {
            "role": "system",
            "content": (
                'Return valid json only, using this structure: '
                '{"question": "string", "answer": "string"}.'
            ),
        },
        {"role": "user", "content": "Which is the longest river? The Nile."},
    ],
    response_format={"type": "json_object"},
    max_tokens=256,
)

content = response.choices[0].message.content
if not content:
    raise ValueError("DeepSeek returned empty content")

result = json.loads(content)
if not {"question", "answer"} <= result.keys():
    raise ValueError("Missing required JSON fields")

print(json.dumps(result, ensure_ascii=False, indent=2))
```

## Agent 示例规范

- 遇到 Agent 相关问题时，可优先查阅知识笔记目录：`/Users/shitou/WWWLLL/obsidian-workspace/30-学习/知识笔记/Agent`。
- 工具定义、模型调用和业务逻辑尽量分离。
- 工具参数应有明确名称、类型和描述，并在执行前进行校验。
- Agent 循环必须设置最大步数，避免无限调用。
- 多轮对话只保留完成任务所需的上下文。
- 不向下一轮消息泄露密钥、内部异常堆栈或无关推理内容。
- 涉及文件修改、命令执行或外部操作时，先校验参数，并限制操作范围。
- 示例默认使用确定、低风险的本地工具；高风险操作必须要求明确确认。

## 修改与验证

修改代码后至少完成以下检查：

```bash
python -m py_compile <file.py>
```

若项目存在测试，则运行对应测试。不能发起真实 API 请求时，应使用 mock 验证：

- 请求地址为 DeepSeek 官方地址。
- 模型名符合本文件约束。
- 消息和工具参数结构正确。
- 响应读取路径与所用 SDK 一致。
- JSON 输出能够被成功解析和校验。

## 官方文档

- 快速开始：https://api-docs.deepseek.com/zh-cn/
- Anthropic API：https://api-docs.deepseek.com/zh-cn/guides/anthropic_api
- JSON Output：https://api-docs.deepseek.com/zh-cn/guides/json_mode/
- Chat Completion：https://api-docs.deepseek.com/api/create-chat-completion

实现方式与本文件冲突或文档已经更新时，以 DeepSeek 官方最新文档为准，同时更新本文件中的示例和约束。
