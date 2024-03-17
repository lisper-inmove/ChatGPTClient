# -*- coding: utf-8 -*-

import grpc
import proto.grpc_api.grpc_chatgpt_pb2 as grpc_chatgpt_pb
import proto.grpc_api.grpc_chatgpt_pb2_grpc as grpc_chatgpt_pb_grpc


def run():
    print("Will try to greet world ...")
    with grpc.secure_channel('openai-client.inmove.top', grpc.ssl_channel_credentials()) as channel:
        stub = grpc_chatgpt_pb_grpc.ChatGPTStub(channel)
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
