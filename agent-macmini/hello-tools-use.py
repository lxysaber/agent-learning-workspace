import os

import anthropic

from response_inspector import ResponseInspector


client = anthropic.Anthropic(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com/anthropic",
)


def main() -> None:
    response = client.messages.create(
        model="deepseek-v4-flash",
        max_tokens=1024,
        tools=[{"type": "web_search_20260209", "name": "web_search"}],
        messages=[
            {"role": "user", "content": "What's the latest on the Mars rover?"}
        ],
    )

    # 工具类会先打印类型地图，再输出过滤加密载荷后的紧凑 JSON。
    inspector = ResponseInspector()
    inspector.print_response(response)


if __name__ == "__main__":
    main()
