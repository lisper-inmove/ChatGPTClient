# -*- coding: utf-8 -*-

import grpc
import proto.grpc_api.grpc_chatgpt_pb2 as grpc_chatgpt_pb
import proto.grpc_api.grpc_chatgpt_pb2_grpc as grpc_chatgpt_pb_grpc


def run():
    print("Will try to greet world ...")
    with grpc.secure_channel('openai-client.inmove.top', grpc.ssl_channel_credentials()) as channel:
        stub = grpc_chatgpt_pb_grpc.ChatGPTStub(channel)
        result = []
        for response in stub.QueryEmbeddingText(grpc_chatgpt_pb.QueryEmbeddingTextRequest(
            text="Chopin 什么时候出生的?",
            indexName="featherpdf",
            fileId="featherpdf"
        )):
            result.append(response.choices[0].delta.content)

        print("".join(result))

if __name__ == '__main__':
    run()
