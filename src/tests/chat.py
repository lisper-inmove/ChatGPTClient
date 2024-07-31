import asyncio
from openai_client import OpenAIClient


async def main():

    identification = """
    1. Your are a programmer
    2. Answer my question using Chinese always.
    """
    settings = [{
        "role": "system",
        "content": identification,
    }]
    messages = []

    while True:
        new_content = input("User: ")

        if new_content in ("Q", "q"):
            break
        if new_content == '':
            continue
        user_message = {"role": "user", "content": new_content}
        messages.append(user_message)

        chatgpt_message = ""
        async for response in client.ChatCompletion({
                "messages": messages,
        }):
            delta = response.choices[0].delta
            if delta.role == "assistant":
                continue
            chatgpt_message += delta.content
        print(f"Assistant: {chatgpt_message}")
        messages.append({"role": "assistant", "content": chatgpt_message})
        if len(messages) >= 50:
            messages = messages[-49:]
            messages.insert(0, settings[0])
        print("-" * 70)

if __name__ == '__main__':
    client = OpenAIClient()
    asyncio.run(main())
