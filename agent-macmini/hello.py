import anthropic

client = anthropic.Anthropic()

message = client.messages.create(
    model="deepseek-v4-flash",
    max_tokens=1000,
    system="You are a helpful assistant.",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Hi, how are you?"
                }
            ]
        },
        {
            "role": "assistant",
            "content": "Hello!"
        },
        {
            "role": "assistant",
            "content": "Can you describe LLMs to me? with chinese."
        }
    ]
)
print(message.content)