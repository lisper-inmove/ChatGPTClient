import random

from openai import AsyncOpenAI

from proto.grpc_api.grpc_chatgpt_pb2 import ChatCompletionResponse
from proto.grpc_api.grpc_chatgpt_pb2_grpc import ChatGPTServicer

from submodules.utils.protobuf_helper import ProtobufHelper as PH
from submodules.utils.sys_env import SysEnv
from submodules.utils.logger import Logger

logger = Logger()


class OpenAIClient(ChatGPTServicer):

    def __init__(self):
        self.api_keys = SysEnv.get("OPENAI_API_KEYS").split(",")
        self.aclient = AsyncOpenAI(api_key=self.api_key)
        # logger.info(f"My App Keys: {self.api_keys}")

    @property
    def api_key(self):
        return self.api_keys[
            random.randint(0, len(self.api_keys)) % (len(self.api_keys))]

    async def ChatCompletion(self, request):
        response = await self.aclient.chat.completions.create(
            model='gpt-4o', messages=request.get('messages'), stream=True)
        async for chunk in response:
            yield PH.to_obj(chunk.dict(), ChatCompletionResponse)
