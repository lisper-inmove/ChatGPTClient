# -*- coding: utf-8 -*-

import grpc
import proto.grpc_api.grpc_chatgpt_pb2 as grpc_chatgpt_pb
import proto.grpc_api.grpc_chatgpt_pb2_grpc as grpc_chatgpt_pb_grpc


def run():
    print("Will try to greet world ...")
    with grpc.secure_channel('openai-client.inmove.top', grpc.ssl_channel_credentials()) as channel:
        stub = grpc_chatgpt_pb_grpc.ChatGPTStub(channel)
        result = stub.EmbeddingPdf(grpc_chatgpt_pb.EmbeddingPdfRequest(
            fileUrl="https://utfs.io/f/5839c6a3-0f81-4233-a8ae-5e3d410ee2a4-8h7jxf.pdf",
            filename="ch02.pdf",
            indexName="featherpdf",
            fileId="featherpdf"
        ))
        print(result)


if __name__ == '__main__':
    run()
