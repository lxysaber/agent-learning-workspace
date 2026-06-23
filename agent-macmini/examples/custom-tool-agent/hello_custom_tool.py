import json
import os
from typing import Any

from openai import OpenAI

from custom_tool import TOOL_DEFINITIONS, execute_tool


MODEL = "deepseek-v4-flash"
MAX_TOOL_STEPS = 5


def create_client() -> OpenAI:
    """创建 DeepSeek 官方 OpenAI 兼容客户端，密钥只从环境变量读取。"""
    return OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )


def run_one_tool_call(tool_call: Any) -> str:
    """执行模型请求的一个工具调用，并把结果转成 tool 消息内容。"""
    if tool_call.type != "function":
        payload = {"ok": False, "error": f"Unsupported tool type: {tool_call.type}"}
        return json.dumps(payload, ensure_ascii=False)

    name = tool_call.function.name
    arguments = tool_call.function.arguments or "{}"

    try:
        result = execute_tool(name, arguments)
        payload = {"ok": True, "result": result}
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        # 工具执行失败也要返回给模型，让模型决定如何向用户解释。
        payload = {"ok": False, "error": str(exc)}

    return json.dumps(payload, ensure_ascii=False)


def assistant_message_to_dict(message: Any) -> dict[str, Any]:
    """把 SDK 返回的 assistant 消息转成下一轮请求可直接使用的字典。"""
    if hasattr(message, "model_dump"):
        return message.model_dump(exclude_none=True)
    if isinstance(message, dict):
        return message

    return {
        "role": "assistant",
        "content": getattr(message, "content", None),
        "tool_calls": getattr(message, "tool_calls", None),
    }


def ask_with_tools(user_input: str) -> str:
    """完整 Agent 循环：模型提出工具调用，Python 执行，再回传结果。"""
    client = create_client()
    messages: list[Any] = [
        {
            "role": "system",
            "content": (
                "你是一个会谨慎使用工具的数学助手。"
                "当问题需要计算两个数字之和时，必须调用 add_numbers 工具。"
            ),
        },
        {"role": "user", "content": user_input},
    ]

    for step in range(1, MAX_TOOL_STEPS + 1):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )
        assistant_message = response.choices[0].message
        messages.append(assistant_message_to_dict(assistant_message))

        tool_calls = assistant_message.tool_calls or []
        if not tool_calls:
            return assistant_message.content or ""

        for tool_call in tool_calls:
            print(
                f"第 {step} 轮工具调用: "
                f"{tool_call.function.name}({tool_call.function.arguments})"
            )
            tool_result = run_one_tool_call(tool_call)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                }
            )

    raise RuntimeError("Tool loop exceeded the maximum number of steps")


def main() -> None:
    """运行示例：让模型决定调用 add_numbers 工具并生成最终回答。"""
    answer = ask_with_tools("请帮我计算 17.5 加 24.8，并说明结果。")
    print(answer)


if __name__ == "__main__":
    main()
