# -*- coding: utf-8 -*-

import grpc
import proto.grpc_api.grpc_chatgpt_pb2 as grpc_chatgpt_pb
import proto.grpc_api.grpc_chatgpt_pb2_grpc as grpc_chatgpt_pb_grpc


def run():
    print("Will try to greet world ...")
    # 1. 创建一条通道与服务端连接
    with grpc.secure_channel('chat.inmove.top:8443', grpc.ssl_channel_credentials()) as channel:
        # 2. 创建一条存根(就当作是创建了一个Hello类)
        stub = grpc_chatgpt_pb_grpc.ChatGPTStub(channel)
        # 3. 调用服务提供的函数,并返回结果
        for response in stub.ChatCompletion(grpc_chatgpt_pb.ChatCompletionRequest(
            messages=[
                grpc_chatgpt_pb.ChatCompletionRequest.ChatCompletionMessage(
                    role="user",
                    content="An solution for leetcode 1001 using Rust"
                )
            ]
        )):
            print(f"role: {response}")


if __name__ == '__main__':
    run()
