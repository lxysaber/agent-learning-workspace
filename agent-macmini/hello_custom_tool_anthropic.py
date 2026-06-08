import json
import os
from typing import Any

import anthropic

from custom_tool import TOOL_DEFINITIONS, execute_tool


MODEL = "deepseek-v4-flash"
MAX_TOOL_STEPS = 5


def create_client() -> anthropic.Anthropic:
    """创建 DeepSeek 官方 Anthropic 兼容客户端，密钥统一读取 DEEPSEEK_API_KEY。"""
    return anthropic.Anthropic(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com/anthropic",
    )


def convert_tools_to_anthropic(openai_tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """把 OpenAI 工具定义转换成 Anthropic Messages API 的工具格式。"""
    anthropic_tools = []

    for tool in openai_tools:
        function = tool["function"]
        anthropic_tools.append(
            {
                "name": function["name"],
                "description": function["description"],
                "input_schema": function["parameters"],
            }
        )

    return anthropic_tools


def to_message_content(blocks: list[Any]) -> list[dict[str, Any]]:
    """把 SDK 内容块转换成下一轮 messages 可以继续使用的字典列表。"""
    content = []

    for block in blocks:
        if hasattr(block, "model_dump"):
            content.append(block.model_dump(exclude_none=True))
        elif isinstance(block, dict):
            content.append(block)
        else:
            content.append(
                {
                    "type": getattr(block, "type", "text"),
                    "text": getattr(block, "text", str(block)),
                }
            )

    return content


def find_text(blocks: list[Any]) -> str:
    """从 Anthropic 内容块中提取最终文本回答。"""
    texts = [
        getattr(block, "text", "")
        for block in blocks
        if getattr(block, "type", None) == "text"
    ]
    return "\n".join(text for text in texts if text)


def find_tool_uses(blocks: list[Any]) -> list[Any]:
    """从模型返回内容里找出所有 tool_use 块。"""
    return [
        block
        for block in blocks
        if getattr(block, "type", None) == "tool_use"
    ]


def run_one_tool_use(tool_use: Any) -> str:
    """执行一个 Anthropic tool_use 内容块，并返回 JSON 字符串结果。"""
    name = tool_use.name
    arguments = tool_use.input or {}

    try:
        result = execute_tool(name, arguments)
        payload = {"ok": True, "result": result}
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        # 工具失败也回传给模型，让模型根据错误信息继续处理。
        payload = {"ok": False, "error": str(exc)}

    return json.dumps(payload, ensure_ascii=False)


def ask_with_tools(user_input: str) -> str:
    """Anthropic SDK 版本的 Agent 循环：tool_use -> tool_result -> 最终回答。"""
    client = create_client()
    tools = convert_tools_to_anthropic(TOOL_DEFINITIONS)
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": user_input},
    ]

    for step in range(1, MAX_TOOL_STEPS + 1):
        message = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=(
                "你是一个会谨慎使用工具的数学助手。"
                "当问题需要计算两个数字之和时，必须调用 add_numbers 工具。"
            ),
            messages=messages,
            tools=tools,
            tool_choice={"type": "auto"},
        )

        messages.append(
            {
                "role": "assistant",
                "content": to_message_content(message.content),
            }
        )

        tool_uses = find_tool_uses(message.content)
        if not tool_uses:
            return find_text(message.content)

        tool_results = []
        for tool_use in tool_uses:
            print(f"第 {step} 轮工具调用: {tool_use.name}({tool_use.input})")
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": run_one_tool_use(tool_use),
                }
            )

        messages.append({"role": "user", "content": tool_results})

    raise RuntimeError("Tool loop exceeded the maximum number of steps")


def main() -> None:
    """运行 Anthropic SDK 示例：让模型调用 add_numbers 并生成最终回答。"""
    answer = ask_with_tools("请帮我计算 17.5 加 24.8，并说明结果。")
    print(answer)


if __name__ == "__main__":
    main()
