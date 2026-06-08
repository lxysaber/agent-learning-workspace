# 自定义工具实现顺序

这个示例从一个最小工具 `add_numbers` 开始，展示 Agent 工具调用的完整闭环。

## 第 1 步：先写普通 Python 函数

文件：[custom_tool.py](custom_tool.py)

先不要管模型，只写真实业务函数：

```python
def add_numbers(a, b):
    return {"a": a, "b": b, "result": a + b}
```

这一步的目标是确认：工具本身离开模型也能工作。

运行：

```bash
python custom_tool.py
```

## 第 2 步：给模型写工具说明书

模型不会读 Python 函数签名，它读取的是 `TOOL_DEFINITIONS` 里的 JSON Schema。

核心字段：

- `type`: 当前 DeepSeek Chat Completion 工具类型使用 `function`
- `function.name`: 工具名，后续必须和注册表一致
- `function.description`: 告诉模型什么时候使用
- `function.parameters`: 告诉模型应该生成哪些参数

## 第 3 步：建立工具注册表

不要让模型传什么函数名就执行什么函数。

示例中使用：

```python
TOOL_REGISTRY = {
    "add_numbers": execute_add_numbers,
}
```

这相当于白名单：只有注册过的工具才能被调用。

## 第 4 步：解析并校验参数

模型返回的参数通常是 JSON 字符串，例如：

```json
{"a": 17.5, "b": 24.8}
```

执行前必须做三件事：

1. 用 `json.loads()` 解析
2. 检查是不是对象
3. 检查字段和类型是否正确

本示例拒绝字符串、布尔值和多余字段，避免错误参数进入真实工具。

## 第 5 步：把工具定义发给 DeepSeek

文件：[hello_custom_tool.py](hello_custom_tool.py)

调用模型时把工具定义放进 `tools`：

```python
response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=messages,
    tools=TOOL_DEFINITIONS,
    tool_choice="auto",
)
```

`tool_choice="auto"` 表示模型可以自己决定是直接回答，还是请求调用工具。

## 第 6 步：读取模型请求的工具调用

模型不会直接执行 Python 函数。它只会返回类似这样的结构：

```text
tool_call.id
tool_call.function.name
tool_call.function.arguments
```

程序要读取这些字段，然后调用本地 `execute_tool()`。

## 第 7 步：把工具结果回传给模型

执行本地函数后，需要追加一条 `role="tool"` 的消息：

```python
messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": tool_result,
})
```

这里的 `tool_call_id` 很重要，它告诉模型：这条结果对应刚才哪一次工具调用。

## 第 8 步：再次请求模型生成最终回答

工具结果只是原始数据。模型拿到结果后，还需要再请求一次，生成面向用户的自然语言回答。

本示例用最多 `MAX_TOOL_STEPS = 5` 步防止无限循环。

运行：

```bash
export DEEPSEEK_API_KEY="你的 key"
python hello_custom_tool.py
```

## 关键理解

自定义工具不是“让模型执行代码”，而是：

1. 模型根据 Schema 生成工具调用请求
2. Python 程序检查并执行真实函数
3. Python 程序把结果返回模型
4. 模型基于工具结果生成最终回答

官方参考：

- DeepSeek Function Calling: https://api-docs.deepseek.com/guides/function_calling/
- DeepSeek Tool Calls: https://api-docs.deepseek.com/guides/tool_calls
- DeepSeek Chat Completion: https://api-docs.deepseek.com/api/create-chat-completion
