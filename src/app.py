# -*- coding: utf-8 -*-

import asyncio
import random

import grpc
from openai import AsyncOpenAI

from proto.grpc_api.grpc_chatgpt_pb2 import ChatCompletionResponse
from proto.grpc_api.grpc_chatgpt_pb2_grpc import ChatGPTServicer
import proto.grpc_api.grpc_chatgpt_pb2_grpc as chatgpt_pb2_grpc

from submodules.utils.protobuf_helper import ProtobufHelper as PH
from submodules.utils.sys_env import SysEnv
from submodules.utils.logger import Logger

logger = Logger()


class ChatGPTClient(ChatGPTServicer):

    def __init__(self):
        self.api_keys = SysEnv.get("OPENAI_API_KEYS").split(",")
        self.aclient = AsyncOpenAI(api_key=self.api_key)
        logger.info(f"My App Keys: {self.api_keys}")

    @property
    def api_key(self):
        return self.api_keys[
            random.randint(0, len(self.api_keys)) % (len(self.api_keys))]

# ChatCompletionChunk(id='chatcmpl-93kKCtm6VfGOvzDTCeSdJMrhi4Fz9', choices=[Choice(delta=ChoiceDelta(content='', function_call=None, role='assistant', tool_calls=None), finish_reason=None, index=0, logprobs=None)], created=1710680084, model='gpt-3.5-turbo-16k-0613', object='chat.completion.chunk', system_fingerprint=None)

    async def ChatCompletion(self, request, context):
        request = PH.to_dict(request)
        response = await self.aclient.chat.completions.create(
            model='gpt-3.5-turbo-16k',
            messages=request.get('messages'),
            stream=True
        )
        async for chunk in response:
            yield PH.to_obj(chunk.dict(), ChatCompletionResponse)

    async def EmbeddingPdf(self, request, context):
        request = PH.to_dict(request)
        print(request)


async def serve() -> None:
    server = grpc.aio.server()
    chatgpt_pb2_grpc.add_ChatGPTServicer_to_server(ChatGPTClient(), server)
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    logger.info(f"Starting server on {listen_addr}")
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
