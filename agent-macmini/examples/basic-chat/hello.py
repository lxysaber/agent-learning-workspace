import os

import anthropic


MODEL = "deepseek-v4-flash"


def create_client() -> anthropic.Anthropic:
    """创建 DeepSeek 官方 Anthropic 兼容客户端，密钥只从环境变量读取。"""
    return anthropic.Anthropic(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com/anthropic",
    )


def main() -> None:
    """运行最小多轮对话示例。"""
    client = create_client()
    message = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system="You are a helpful assistant.",
        messages=[
            {
                "role": "user",
                "content": "Hi, how are you?",
            },
            {
                "role": "assistant",
                "content": "Hello!",
            },
            {
                "role": "user",
                "content": "Can you describe LLMs to me? with chinese.",
            },
        ],
    )
    print(message.content)


if __name__ == "__main__":
    main()
