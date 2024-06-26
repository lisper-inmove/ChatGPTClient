"""start as websocket server"""

import time
from typing import List

import asyncio
import json
import random
import psutil

import websockets
from openai import AsyncOpenAI
from pinecone_client.client import query_index, upsert_index
from langchain.text_splitter import CharacterTextSplitter

import proto.api.api_common_pb2 as api_common_pb
import proto.api.api_featherpdf_pb2 as api_featherpdf_pb
import proto.api.api_chitchat_pb2 as api_chitchat_pb
from constants import openai as openai_constants
from submodules.utils.idate import IDate
from submodules.utils.pdf_util import download_pdf_async, read_pdf_sync_v2
from submodules.utils.protobuf_helper import ProtobufHelper as PH
from submodules.utils.logger import Logger
from submodules.utils.sys_env import SysEnv
from submodules.utils.profile import func_time_expend_async
from session import Session

logger = Logger()


class Server:

    def __init__(self):
        self.api_keys = SysEnv.get("OPENAI_API_KEYS").split(",")
        self.aclient = AsyncOpenAI(api_key=self.api_key)
        self.client_count = 0

    @property
    def api_key(self):
        return self.api_keys[
            random.randint(0, len(self.api_keys)) % (len(self.api_keys))]

    async def handle_connection(self, conn, path):
        try:
            setattr(conn, "session", Session())
            self.client_count += 1
            await self.__handle_connection(conn, path)
        except websockets.ConnectionClosed as ex:
            logger.error(f"Connection Closed: {ex}")
            self.client_count -= 1

    async def __handle_connection(self, conn, path: str):
        logger.info(f"new connection: {conn}")
        while True:
            async for message_json in conn:
                logger.info(f"get message: {message_json}")
                request = api_common_pb.Request()
                request.ParseFromString(message_json)
                response = None
                if (request.action == api_common_pb.Action.EMBEDDING_PDF):
                    response = self.__handle_embedding_pdf_request(request)
                elif (request.action == api_common_pb.Action.EMBEDDING_QUERY_TEXT):
                    response = self.__handle_embedding_query_text_request(request)
                logger.info(f"{request} --- {response}")
                if response is not None:
                    async for r in response:
                        data = PH.to_json(r)
                        logger.info(f"Send back: {data}")
                        await conn.send(json.dumps(data))
            await conn.ping()

    async def __process_embedding(self, body, index, splitted_content):
        res = await self.aclient.embeddings.create(
            input=splitted_content,
            model=openai_constants.MODEL_TEXT_EMBEDDING_ADA_002
        )
        embeds = [record.embedding for record in res.data]
        logger.info(f"Embedding content: {index}")
        await upsert_index(embeds[0], splitted_content, body.indexName, f"{body.fileId}-{index}")

    @func_time_expend_async
    async def __handle_embedding_pdf_request(self, request: api_common_pb.Request):
        body = PH.to_obj(json.loads(request.content), api_featherpdf_pb.EmbeddingPdfRequest)
        pdf_path = await download_pdf_async(body.fileUrl, body.filename)
        content = read_pdf_sync_v2(pdf_path)
        content_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=800,
            chunk_overlap=200,
            length_function=len
        )
        splitted_contents = content_splitter.split_text(content)
        tasks = []
        for index, splitted_content in enumerate(splitted_contents):
            tasks.append(self.__process_embedding(body, index, splitted_content))
        await asyncio.gather(*tasks)

        messages = [
            {
                'role': "user",
                "content": f"""
                    Summarize this abstract delimited by triple slashes in 5 sentences less than 500 words in markdown mode.
                    1. Just give me pure text response.
                    2. Highlight high frequency words if they are contained in the summary.
                    ///{content}///
                """
            }
        ]
        conspectus = ""
        async for data in self.ask_gpt4(messages):
            conspectus += data.content
        response = api_featherpdf_pb.EmbeddingPdfResponse()
        response.conspectus = conspectus

        # response = api_featherpdf_pb.EmbeddingPdfResponse()

        yield self.__wrap_response(response, action=api_common_pb.Action.EMBEDDING_PDF_RESPONSE)

    @func_time_expend_async
    async def __handle_embedding_query_text_request(self, request: api_common_pb.Request):
        body = PH.to_obj(json.loads(request.content), api_featherpdf_pb.QueryTextRequest)
        res = await self.aclient.embeddings.create(
            input=body.text,
            model=openai_constants.MODEL_TEXT_EMBEDDING_ADA_002
        )
        embeds = [record.embedding for record in res.data]
        queryResult = query_index(embeds[0], body.indexName, body.fileId)
        messageContent = []
        for match in queryResult['matches']:
            metadata = match['metadata']
            content = metadata["content"]
            score = match["score"]
            # logger.info(f"{body.text} {score} {content}")
            if (score <= 0.75):
                continue
            messageContent.append(content)
        # logger.info(f"messageContent: {' '.join(messageContent)}")
        if len(messageContent) == 0:
            data = api_chitchat_pb.ChitchatCommonResponse()
            data.role = "assistant"
            yield self.__wrap_response(data, api_common_pb.Action.EMBEDDING_QUERY_RESPONSE)
            data = api_chitchat_pb.ChitchatCommonResponse()
            data.content = "Sorry, i can't find any answer."
            yield self.__wrap_response(data, api_common_pb.Action.EMBEDDING_QUERY_RESPONSE)
            data = api_chitchat_pb.ChitchatCommonResponse()
            data.finishReason = "stop"
            yield self.__wrap_response(data, api_common_pb.Action.EMBEDDING_QUERY_RESPONSE)
        else:
            messages = [
                {
                    'role': 'system',
                    'content': 'Use the following pieces of context to answer the users question in markdown format.',
                },
                {
                    'role': "user",
                    "content": f"""CONTENT: {" ".join(messageContent)} USER_INPUT: {body.text}"""
                },
            ]
            async for data in self.ask_gpt4(messages):
                yield self.__wrap_response(data, action=api_common_pb.Action.EMBEDDING_QUERY_RESPONSE)

    @func_time_expend_async
    async def ask_gpt4(self, messages: List, stream: bool | None = None):
        if (stream is None):
            stream = True
        response = await self.aclient.chat.completions.create(
            model=openai_constants.MODEL_GPT_4_TURBO_PREVIEW,
            messages=messages,
            stream=stream
        )
        async for chunk in response:
            # logger.info(f"opneai response: {chunk}")
            data = api_chitchat_pb.ChitchatCommonResponse()
            choice = chunk.choices[0]
            delta = choice.delta
            data.role = delta.role or ''
            data.content = delta.content or ''
            data.finishReason = choice.finish_reason or ''
            data.index = choice.index or 0
            data.model = chunk.model or ''
            yield data

    async def watcher(self):
        while True:
            cpu_percent = psutil.cpu_percent(percpu=True)
            memory_percent = psutil.virtual_memory().percent
            logger.info(f"""
                cpu: {cpu_percent}
                mem: {memory_percent}
                conn: {self.client_count}
            """)
            await asyncio.sleep(5)

    def __wrap_response(self, data, action: api_common_pb.Action):
        response = api_common_pb.Response()
        response.action = action
        response.content = json.dumps(PH.to_json(data));
        return response


async def main(host = "0.0.0.0", port = 50052):
    server = Server()
    task_websocket = websockets.serve(server.handle_connection, host, port)
    task_watcher = asyncio.create_task(server.watcher())
    await asyncio.gather(task_websocket, task_watcher)


if __name__ == "__main__":
    asyncio.run(main())
