import asyncio

from openai_client import OpenAIClient
from rich.console import Console
from rich.markdown import Markdown


class ColorPrinter:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    BLACK_FONT_C = "\033[30m"
    RED_FONT_C = "\033[31m"
    GREEN_FONT_C = "\033[32m"
    YELLOW_FONT_C = "\033[33m"
    DARK_BLUE_FONT_C = "\033[34m"
    PINK_FONT_C = "\033[35m"
    LIGHT_BLUE_FONT_C = "\033[36m"
    LIGHT_GREY_FONT_C = "\033[90m"
    ORIGIN_FONT_C = "\033[91m"

    @classmethod
    def color_value(cls, color, value):
        return color + str(value) + cls.ENDC

    @classmethod
    def red_value(cls, value):
        return cls.color_value(cls.RED_FONT_C, value)

    @classmethod
    def green_value(cls, value):
        return cls.color_value(cls.GREEN_FONT_C, value)

    @classmethod
    def pink_value(cls, value):
        return cls.color_value(cls.PINK_FONT_C, value)


async def main():

    identification = """
    1. Your are a programmer
    2. Answer my question using Chinese always.
    """
    settings = [{
        "role": "system",
        "content": identification,
    }]
    messages = [settings[0]]

    console = Console()

    while True:
        new_content = input("User: ")
        if new_content in ("Q", "q"):
            break
        if new_content in ("c", "C"):
            messages = [settings[0]]
            continue
        if new_content == '':
            continue
        print(ColorPrinter.pink_value('-' * 120))
        value = f"User: {new_content}"
        print(ColorPrinter.red_value(value))
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
        md = Markdown(chatgpt_message)
        console.print(md)
        messages.append({"role": "assistant", "content": chatgpt_message})
        if len(messages) >= 50:
            messages = messages[-49:]
            messages.insert(0, settings[0])
        print(ColorPrinter.green_value('-' * 120))

if __name__ == '__main__':
    client = OpenAIClient()
    asyncio.run(main())
