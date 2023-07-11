# -*- coding: utf-8 -*-

import random
from concurrent import futures

import grpc
import openai
from proto.grpc_api.grpc_chatgpt_pb2 import ChatCompletionResponse
from proto.grpc_api.grpc_chatgpt_pb2_grpc import ChatGPTServicer
import proto.grpc_api.grpc_chatgpt_pb2_grpc as chatgpt_pb2_grpc

from submodules.utils.protobuf_helper import ProtobufHelper as PH
from submodules.utils.sys_env import SysEnv
from submodules.utils.logger import Logger

logger = Logger()


class ChatGPTClient(ChatGPTServicer):

    def __init__(self):
        self.api_keys = SysEnv.get("CHAT_GPT_API_KEYS").split(",")
        logger.info(f"My App Keys: {self.api_keys}")

    @property
    def api_key(self):
        return self.api_keys[
            random.randint(0, len(self.api_keys)) % (len(self.api_keys))]

    def ChatCompletion(self, request, context):
        request = PH.to_dict(request)
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo-16k',
            messages=request.get('messages'),
            stream=True,
            api_key=self.api_key
        )
        for chunk in response:
            yield PH.to_obj(chunk, ChatCompletionResponse)

def serve() -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5000))
    chatgpt_pb2_grpc.add_ChatGPTServicer_to_server(ChatGPTClient(), server)
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    logger.info(f"Starting server on {listen_addr}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
