---
title: custom_tool.py 逐行解释
tags:
  - agent
  - python
  - tool-calling
aliases:
  - custom_tool.py 代码讲解
---

# custom_tool.py 逐行解释

文件：[custom_tool.py](custom_tool.py)

你觉得这段 Python 怪很正常，因为这个文件里混了三类东西：

- Python 基础语法
- 类型标注
- 给模型看的 JSON Schema

先抓住一句话：这个文件不是模型代码，它是在 Python 里定义“工具是什么、参数怎么校验、怎么安全执行”。

## 整体结构

1. 第 1-7 行：导入模块，定义类型别名。
2. 第 10-16 行：真正的工具函数 `add_numbers`。
3. 第 19-43 行：给模型看的工具说明书。
4. 第 46-89 行：参数校验和工具执行入口。
5. 第 92-99 行：本地测试入口。

## 第 1 行

```python
import json
```

导入 Python 内置的 `json` 模块。

它的作用是：

- 把 JSON 字符串转成 Python 字典
- 把 Python 字典转成 JSON 字符串

## 第 2 行

```python
from collections.abc import Callable
```

导入 `Callable`。

`Callable` 表示“一个可以被调用的东西”，通常就是函数。

## 第 3 行

```python
from typing import Any
```

导入 `Any`。

`Any` 表示“任意类型”，比如字符串、数字、列表、字典都可以。

## 第 6 行

```python
ToolResult = dict[str, Any]
```

这是类型别名。

意思是：以后代码里看到 `ToolResult`，就理解成：

```python
dict[str, Any]
```

也就是“键是字符串，值可以是任意类型的字典”。

## 第 7 行

```python
ToolExecutor = Callable[[dict[str, Any]], ToolResult]
```

这也是类型别名。

意思是：工具执行函数应该满足这个形状：

- 接收一个字典参数
- 返回一个 `ToolResult` 字典

可以粗略理解成：

```python
def some_tool(arguments: dict[str, Any]) -> ToolResult:
    ...
```

## 第 10 行

```python
def add_numbers(a: int | float, b: int | float) -> ToolResult:
```

定义一个函数，函数名是 `add_numbers`。

参数：

- `a: int | float`：`a` 可以是整数或小数
- `b: int | float`：`b` 可以是整数或小数

返回值：

- `-> ToolResult`：预计返回一个字典

其中 `|` 表示“或者”。所以 `int | float` 就是“整数或者小数”。

## 第 11 行

```python
"""执行真正的本地业务逻辑：把两个数字相加。"""
```

这是函数说明，Python 里叫 docstring。

三引号字符串放在函数开头时，用来说明这个函数的用途。

## 第 12-16 行

```python
return {
    "a": a,
    "b": b,
    "result": a + b,
}
```

返回一个字典。

如果调用：

```python
add_numbers(2, 3)
```

会返回：

```python
{
    "a": 2,
    "b": 3,
    "result": 5,
}
```

## 第 19 行

```python
# 这段 JSON Schema 是给模型看的“工具说明书”，不是 Python 执行逻辑。
```

这是注释。

`#` 后面的内容 Python 不会执行，只是给人看的说明。

## 第 20-41 行

```python
ADD_NUMBERS_TOOL = {
    ...
}
```

这是给模型看的工具说明书。

模型不会直接看 Python 函数，它看的是这段 JSON Schema。

## 第 21 行

```python
"type": "function",
```

告诉 DeepSeek：这是一个函数工具。

## 第 22 行

```python
"function": {
```

函数工具的具体定义都写在这个对象里。

## 第 23 行

```python
"name": "add_numbers",
```

工具名。

模型想调用这个工具时，会生成类似这样的请求：

```json
{
  "name": "add_numbers",
  "arguments": {"a": 1, "b": 2}
}
```

## 第 24 行

```python
"description": "把两个数字相加，并返回计算结果。",
```

工具描述。

这句话会影响模型是否知道什么时候该使用这个工具。

## 第 25 行

```python
"parameters": {
```

开始定义工具参数。

## 第 26 行

```python
"type": "object",
```

表示参数整体必须是一个对象，也就是类似：

```json
{"a": 1, "b": 2}
```

## 第 27-36 行

```python
"properties": {
    "a": {
        "type": "number",
        "description": "第一个数字。",
    },
    "b": {
        "type": "number",
        "description": "第二个数字。",
    },
},
```

定义参数 `a` 和 `b`。

它们的类型都是 `number`，也就是数字。

## 第 37 行

```python
"required": ["a", "b"],
```

表示 `a` 和 `b` 都必须提供。

模型不能只传一个参数。

## 第 38 行

```python
"additionalProperties": False,
```

表示不允许多传其他参数。

这个参数会被拒绝：

```json
{"a": 1, "b": 2, "c": 3}
```

## 第 43 行

```python
TOOL_DEFINITIONS = [ADD_NUMBERS_TOOL]
```

把工具说明书放进列表里。

发给 DeepSeek 的 `tools` 参数需要的是一个工具列表，所以即使现在只有一个工具，也要写成列表。

## 第 46 行

```python
def require_number(name: str, value: Any) -> int | float:
```

定义一个校验函数。

参数：

- `name: str`：参数名，比如 `"a"`
- `value: Any`：参数值，类型暂时未知

返回值：

- `-> int | float`：校验通过后，返回整数或小数

## 第 47 行

```python
"""校验模型传入的参数，避免把布尔值、字符串等错误类型当成数字。"""
```

说明这个函数用来校验参数类型。

## 第 48 行

```python
if isinstance(value, bool) or not isinstance(value, (int, float)):
```

这行是在判断参数是不是不合格。

拆开看：

```python
isinstance(value, bool)
```

判断 `value` 是不是布尔值，比如 `True` 或 `False`。

```python
not isinstance(value, (int, float))
```

判断 `value` 不是整数也不是小数。

这里特意排除了 `bool`，因为 Python 里 `True` 和 `False` 比较特殊，它们也算数字的一种。这个示例不希望模型传 `true` 当数字。

## 第 49 行

```python
raise ValueError(f"{name} must be a number")
```

主动报错。

`ValueError` 表示“值不合法”。

`f"{name} must be a number"` 是 f-string，可以把变量塞进字符串里。

如果 `name` 是 `"a"`，报错内容就是：

```text
a must be a number
```

## 第 50 行

```python
return value
```

校验通过后，把值返回。

## 第 53 行

```python
def execute_add_numbers(arguments: dict[str, Any]) -> ToolResult:
```

这是 `add_numbers` 的安全执行包装器。

它接收模型传来的参数字典，先检查，再调用真正的函数。

## 第 55 行

```python
expected_keys = {"a", "b"}
```

这是集合，表示只允许两个字段：`a` 和 `b`。

集合用 `{}` 表示，特点是不关心顺序，只关心里面有什么。

## 第 56 行

```python
if set(arguments) != expected_keys:
```

`set(arguments)` 会取出字典的所有 key。

例如：

```python
set({"a": 1, "b": 2})
```

会得到：

```python
{"a", "b"}
```

所以这一行是在检查：模型传来的字段是不是刚好只有 `a` 和 `b`。

## 第 57 行

```python
raise ValueError(f"add_numbers expects exactly these keys: {expected_keys}")
```

如果字段不对，就报错。

## 第 59-60 行

```python
a = require_number("a", arguments["a"])
b = require_number("b", arguments["b"])
```

从参数字典里取出 `a` 和 `b`，并检查它们是不是数字。

`arguments["a"]` 表示从字典里取出 key 为 `"a"` 的值。

## 第 61 行

```python
return add_numbers(a, b)
```

真正调用工具函数。

## 第 64 行

```python
# 工具注册表是安全白名单：模型只能调用这里登记过的函数。
```

注释说明下面这个注册表的用途。

## 第 65-67 行

```python
TOOL_REGISTRY: dict[str, ToolExecutor] = {
    "add_numbers": execute_add_numbers,
}
```

这是工具注册表，也就是白名单。

重点是：

```python
"add_numbers": execute_add_numbers
```

左边是模型会请求调用的工具名。

右边是 Python 里真正负责执行的函数。

注意这里没有括号：

```python
execute_add_numbers
```

表示“保存这个函数本身”。

如果写成：

```python
execute_add_numbers()
```

那就是“现在立刻执行这个函数”。

## 第 70 行

```python
def parse_tool_arguments(raw_arguments: str | dict[str, Any]) -> dict[str, Any]:
```

定义参数解析函数。

模型传来的参数可能是：

- JSON 字符串
- 已经解析好的 Python 字典

这个函数负责统一转成字典。

## 第 72-73 行

```python
if isinstance(raw_arguments, dict):
    return raw_arguments
```

如果参数已经是字典，就直接返回。

## 第 74-75 行

```python
if not raw_arguments:
    return {}
```

如果参数为空，就返回空字典。

比如这些都算“空”：

```python
""
None
{}
```

## 第 77 行

```python
parsed = json.loads(raw_arguments)
```

把 JSON 字符串解析成 Python 对象。

例如：

```python
'{"a": 1, "b": 2}'
```

会变成：

```python
{"a": 1, "b": 2}
```

## 第 78-79 行

```python
if not isinstance(parsed, dict):
    raise ValueError("Tool arguments must be a JSON object")
```

检查解析结果必须是字典。

如果模型传来的是列表、字符串或数字，就拒绝。

## 第 80 行

```python
return parsed
```

返回解析后的字典。

## 第 83 行

```python
def execute_tool(name: str, raw_arguments: str | dict[str, Any]) -> ToolResult:
```

这是统一工具入口。

外部代码只需要调用它，不用关心具体工具怎么校验。

## 第 85-86 行

```python
if name not in TOOL_REGISTRY:
    raise ValueError(f"Unknown tool: {name}")
```

如果模型想调用未注册工具，直接拒绝。

这一步很重要，因为不能让模型传什么函数名就执行什么函数。

## 第 88 行

```python
arguments = parse_tool_arguments(raw_arguments)
```

先把参数转成字典。

## 第 89 行

```python
return TOOL_REGISTRY[name](arguments)
```

这行看起来最怪。

拆开就是：

```python
tool_function = TOOL_REGISTRY[name]
return tool_function(arguments)
```

也就是：

1. 根据工具名找到对应函数
2. 把参数传给这个函数
3. 返回函数执行结果

## 第 92 行

```python
def main() -> None:
```

定义主函数。

`-> None` 表示这个函数不返回值。

## 第 93 行

```python
"""本地自测入口：不调用模型，只验证工具本身是否工作。"""
```

说明 `main()` 的用途：本地测试。

## 第 94 行

```python
result = execute_tool("add_numbers", {"a": 2, "b": 3})
```

模拟模型调用 `add_numbers` 工具。

它等价于：

```python
execute_add_numbers({"a": 2, "b": 3})
```

最终会调用：

```python
add_numbers(2, 3)
```

## 第 95 行

```python
print(json.dumps(result, ensure_ascii=False, indent=2))
```

把结果漂亮地打印成 JSON。

参数说明：

- `ensure_ascii=False`：允许中文正常显示
- `indent=2`：缩进 2 个空格

## 第 98-99 行

```python
if __name__ == "__main__":
    main()
```

这句是 Python 脚本常见写法。

意思是：

- 如果你直接运行这个文件，就执行 `main()`
- 如果别的文件 `import custom_tool`，就不会自动执行 `main()`

## 最核心的三句

```python
TOOL_DEFINITIONS = [ADD_NUMBERS_TOOL]
TOOL_REGISTRY = {"add_numbers": execute_add_numbers}
execute_tool("add_numbers", {"a": 2, "b": 3})
```

分别对应：

1. `TOOL_DEFINITIONS`：给模型看
2. `TOOL_REGISTRY`：给 Python 安全执行用
3. `execute_tool(...)`：真正执行工具

## 一句话总结

自定义工具的核心流程是：

```text
模型看到 TOOL_DEFINITIONS
模型请求调用 add_numbers
Python 在 TOOL_REGISTRY 里找到 execute_add_numbers
execute_add_numbers 校验参数
add_numbers 执行真实计算
Python 把结果返回给模型
```
