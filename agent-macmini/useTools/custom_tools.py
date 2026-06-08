
import json
from collections.abc import Callable
from typing import Any

ToolResult = dict[str, Any]
#工具执行函数接收一个字典参数，返回一个 ToolResult 字典
ToolExecutor = Callable[[dict[str, Any]], ToolResult] 

def add_numbers(a: int | float, b: int | float) -> ToolResult:
    """执行真正的本地业务逻辑：把两个数字相加。"""
    return{
        "a": a,
        "b": b,
        "result": a + b
    }

# 这段 JSON Schema 是给模型看的“工具说明书”，不是 Python 执行逻辑。
ADD_NUMBERS_TOOL = {
    "type": "function",
    "function":{
        "name": "add_numbers",
        "description": "把两个数字相加，并返回计算结果。",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "number",
                    "description": "第一个数字。"
                },
                 "b": {
                    "type": "number",
                    "description": "第二个数字。",
                },
            },
            "required": ["a","b"],
            "additionalProperties": False
        }
    }
}

TOOL_DEFINITIONS = [ADD_NUMBERS_TOOL]

def require_number(name: str, value: Any) -> int | float:
    """校验模型传入的参数，避免把布尔值、字符串等错误类型当成数字。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    return value

def excute_add_numbers(arguments: dict[str, Any]) -> ToolResult:
    """把模型传入的 JSON 参数转换为安全的 Python 函数调用。"""
    expected_keys = {"a", "b"}
    if set(arguments) != expected_keys:
         raise ValueError(f"add_numbers expects exactly these keys: {expected_keys}")
    
    a = require_number("a", arguments["a"])
    b = require_number("b", arguments["b"])
    return add_numbers(a, b)

# 工具注册表是安全白名单：模型只能调用这里登记过的函数
TOOL_REGISTRY: dict[str, ToolExecutor] = {
    "add_numbers": excute_add_numbers,
}

def parse_tool_arguments(raw_arguments: str | dict[str, Any]) -> dict[str, Any]:
      """把模型生成的 JSON 字符串参数解析成字典，便于后续校验。"""
      if isinstance(raw_arguments, dict):
           return raw_arguments
      if not raw_arguments:
           return {}
      
      parsed = json.load(raw_arguments)
      if not isinstance(parsed, dict):
           raise ValueError("Tool arguments must be a JSON object")
      return parsed

def execute_tool(name: str, raw_arguments: str | dict[str, Any]) -> ToolResult:
     """统一工具入口：检查工具名、解析参数、执行本地函数。"""
     if name not in TOOL_REGISTRY:
          raise ValueError(f"Unknown tool: {name}")
     
     arguments = parse_tool_arguments(raw_arguments)
     return TOOL_REGISTRY[name](arguments)

def main() -> None:
      """本地自测入口：不调用模型，只验证工具本身是否工作。"""
      result = execute_tool("add_numbers", {"a": 2, "b": 3})
      print(json.dumps(result, ensure_ascii=False, indent=2))