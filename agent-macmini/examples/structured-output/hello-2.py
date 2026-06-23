import json
import os
from typing import Any

from openai import OpenAI


MODEL = "deepseek-v4-flash"


def create_client() -> OpenAI:
    """创建 DeepSeek 官方 OpenAI 兼容客户端，密钥只从环境变量读取。"""
    return OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )


def parse_exam_text(text: str) -> dict[str, Any]:
    """使用 DeepSeek JSON Output 模式解析题目和答案。"""
    client = create_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Return valid json only. Parse the user's exam text into "
                    'this json structure: {"question": "string", '
                    '"answer": "string"}. Both fields are required.'
                ),
            },
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
        max_tokens=256,
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("DeepSeek returned empty content")

    result = json.loads(content)
    required = {"question", "answer"}
    if not required <= result.keys():
        raise ValueError("Missing required JSON fields")

    return result


def main() -> None:
    """运行结构化输出示例，并打印校验后的 JSON。"""
    user_prompt = "Which is the longest river in the world? The Nile River."
    result = parse_exam_text(user_prompt)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
