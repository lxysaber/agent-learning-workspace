import json
import os

from openai import OpenAI


MODEL = "deepseek-v4-flash"

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

# 1. 定义一个模型可以调用的工具列表
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_horoscope",
            "description": "获取某个星座今天的星座运势。",
            "parameters": {
                "type": "object",
                "properties": {
                    "sign": {
                        "type": "string",
                        "description": "星座名称，例如金牛座或水瓶座",
                    },
                },
                "required": ["sign"],
            },
        },
    },
]


def get_horoscope(sign):
    return f"{sign}: 下周二你会遇到一件让你微笑的小幸运。"


# 创建一个持续累积的消息列表，后续会不断追加模型和工具消息
input_list = [
    {"role": "user", "content": "我的星座运势是什么？我是水瓶座。"}
]

# 2. 带着工具定义提示模型，让模型决定是否调用工具
response = client.chat.completions.create(
    model=MODEL,
    messages=input_list,
    tools=tools,
    tool_choice="auto",
    stream=False,
)

assistant_message = response.choices[0].message

# 保存模型消息，供下一轮请求继续使用
input_list.append(assistant_message.model_dump(exclude_none=True))

for tool_call in assistant_message.tool_calls or []:
    if tool_call.type == "function":
        if tool_call.function.name == "get_horoscope":
            # 3. 执行 get_horoscope 对应的本地函数逻辑
            sign = json.loads(tool_call.function.arguments or "{}")["sign"]
            horoscope = get_horoscope(sign)

            # 4. 把函数调用结果作为 tool 消息回传给模型
            input_list.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": horoscope,
            })

print("最终输入:")
print(input_list)

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "请只返回工具生成的星座运势。"},
        *input_list,
    ],
    tools=tools,
    tool_choice="auto",
    stream=False,
)

# 5. 此时模型应该能根据工具结果给出最终回答
print("最终输出:")
print(response.model_dump_json(indent=2))
print("\n" + (response.choices[0].message.content or ""))
