import json
import os
from typing import Any

import anthropic


client = anthropic.Anthropic(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com/anthropic",
)

RESULT_TOOL = {
    "name": "emit_agent_result",
    "description": "输出 Agent 的最终结构化结果。",
    "input_schema": {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "confidence": {"type": "number"},
            "next_actions": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["answer", "confidence", "next_actions"],
        "additionalProperties": False,
    },
}


def ask_agent(question: str) -> dict[str, Any]:
    """使用强制工具调用，让模型按 JSON Schema 返回结构化结果。"""
    message = client.messages.create(
        model="deepseek-v4-flash",
        max_tokens=1024,
        temperature=0,
        system=(
            "你是结构化输出 Agent。必须调用 emit_agent_result 工具返回最终结果，"
            "不要在普通文本中输出答案。"
        ),
        messages=[
            {"role": "user", "content": question},
        ],
        tools=[RESULT_TOOL],
        # DeepSeek 的思考模式默认开启；强制指定某个工具时需要关闭思考模式。
        thinking={"type": "disabled"},
        tool_choice={"type": "tool", "name": "emit_agent_result"},
    )

    for block in message.content:
        if block.type == "tool_use" and block.name == "emit_agent_result":
            result = block.input
            required = {"answer", "confidence", "next_actions"}
            if not required <= result.keys():
                raise ValueError("模型返回缺少必需字段")
            return result

    raise ValueError("模型没有返回预期的 tool_use 结构")


if __name__ == "__main__":
    result = ask_agent("给我解释一下什么是 Agent 工具调用。")
    print(json.dumps(result, ensure_ascii=False, indent=2))
