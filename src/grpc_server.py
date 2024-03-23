"""start as grpc server"""

import asyncio
import random

import grpc
from openai import AsyncOpenAI

import proto.grpc_api.grpc_chatgpt_pb2_grpc as chatgpt_pb2_grpc
from proto.grpc_api.grpc_chatgpt_pb2 import ChatCompletionResponse
from proto.grpc_api.grpc_chatgpt_pb2 import EmbeddingPdfRequest, EmbeddingPdfResponse
from proto.grpc_api.grpc_chatgpt_pb2 import QueryEmbeddingTextResponse
from proto.grpc_api.grpc_chatgpt_pb2_grpc import ChatGPTServicer

from pinecone_client.client import upsert_index, query_index

from submodules.utils.protobuf_helper import ProtobufHelper as PH
from submodules.utils.sys_env import SysEnv
from submodules.utils.logger import Logger
from submodules.utils.pdf_util import download_pdf_async, read_pdf_sync

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

    async def ChatCompletion(self, request, context):
        request = PH.to_dict(request)
        response = await self.aclient.chat.completions.create(
            model='gpt-3.5-turbo-16k',
            messages=request.get('messages'),
            stream=True
        )
        async for chunk in response:
            yield PH.to_obj(chunk.dict(), ChatCompletionResponse)

    async def EmbeddingPdf(self, request: EmbeddingPdfRequest, context):
        pdf_path = await download_pdf_async(request.fileUrl, request.filename)
        contents = read_pdf_sync(pdf_path)
        for index, content in enumerate(contents):
            res = await self.aclient.embeddings.create(input=content, model="text-embedding-ada-002")
            embeds = [record.embedding for record in res.data]
            upsert_index(embeds[0], content, request.indexName, f"{request.fileId}-{index}")
        return EmbeddingPdfResponse()

    async def QueryEmbeddingText(self, request: QueryEmbeddingTextRequest, context):
        res = await self.aclient.embeddings.create(input=request.text, model="text-embedding-ada-002")
        embeds = [record.embedding for record in res.data]
        queryResult = query_index(embeds[0], request.indexName, request.fileId)
        messageContent = []
        for match in queryResult['matches']:
            metadata = match['metadata']
            content = metadata["content"]
            score = match["score"]
            if (score <= 0.81):
                continue
            messageContent.append(content)
        messages = [
            {
                'role': 'system',
                'content': 'Use the following pieces of context (or previous conversaton if needed) to answer the users question in markdown format.',
            },
            # previous messages
            {
                'role': "user",
                "content": f"""CONTENT: {messageContent[0]} USER_INPUT: {request.text}"""
            },
        ]
        response = await self.aclient.chat.completions.create(
            model='gpt-3.5-turbo-16k',
            messages=messages,
            stream=True
        )
        async for chunk in response:
            yield PH.to_obj(chunk.model_dump(), ChatCompletionResponse)

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
