# -*- coding: utf-8 -*-

import grpc
import api.chat_completion_pb2 as chat_completion_pb
import api.chat_completion_pb2_grpc as chat_completion_pb_grpc


def run():
    print("Will try to greet world ...")
    # 1. 创建一条通道与服务端连接
    with grpc.insecure_channel('chat.inmove.top:50051') as channel:
        # 2. 创建一条存根(就当作是创建了一个Hello类)
        stub = chat_completion_pb_grpc.ChatCompletionStub(channel)
        # 3. 调用服务提供的函数,并返回结果
        for response in stub.Chat(chat_completion_pb.ChatRequest(
            messages=[
                chat_completion_pb.ChatMessage(
                    role="user",
                    content="Hello Write a hello world using Rust"
                )
            ]
        )):
            print(f"role: {response}")


if __name__ == '__main__':
    run()
