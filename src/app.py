# -*- coding: utf-8 -*-

from concurrent import futures

import grpc
import openai
from api.chat_completion_pb2 import ChatResponse
from api.chat_completion_pb2_grpc import ChatCompletionServicer
import api.chat_completion_pb2_grpc as chat_completion_pb2_grpc

from submodules.utils.protobuf_helper import ProtobufHelper as PH


class ChatCompletion(ChatCompletionServicer):

    api_key = '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'

    def Chat(self, request, context):
        request = PH.to_dict(request)
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo-16k',
            messages=request.get('messages'),
            stream=True,
            api_key=self.api_key
        )
        for chunk in response:
            yield PH.to_obj(chunk, ChatResponse)

def serve() -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5000))
    chat_completion_pb2_grpc.add_ChatCompletionServicer_to_server(
            ChatCompletion(), server)
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    print("Starting server on %s", listen_addr)
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
