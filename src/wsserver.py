"""start as websocket server"""

import asyncio
import json
import os
import random

from openai import AsyncOpenAI
import websockets
from pinecone_client.client import query_index, upsert_index
import proto.api.api_common_pb2 as api_common_pb
import proto.api.api_featherpdf_pb2 as api_featherpdf_pb
import proto.api.api_chitchat_pb2 as api_chitchat_pb
from submodules.utils.pdf_util import download_pdf_async, read_pdf_sync_v3
from submodules.utils.protobuf_helper import ProtobufHelper as PH
from submodules.utils.logger import Logger
from submodules.utils.sys_env import SysEnv
from session import Session

logger = Logger()


class Server:

    def __init__(self, host="0.0.0.0", port=50052):
        self.server = websockets.serve(self.handle_connection, host, port)
        self.api_keys = SysEnv.get("OPENAI_API_KEYS").split(",")
        self.aclient = AsyncOpenAI(api_key=self.api_key)

    @property
    def api_key(self):
        return self.api_keys[
            random.randint(0, len(self.api_keys)) % (len(self.api_keys))]

    async def handle_connection(self, websocket, path):
        try:
            setattr(websocket, "session", Session())
            await self.__handle_connection(websocket, path)
        except websockets.ConnectionClosed as ex:
            logger.error(f"Connection Closed: {ex}")

    async def __handle_connection(self, websocket, path):
        logger.info(f"new connection: {websocket}");
        async for message_json in websocket:
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
                    await websocket.send(json.dumps(data))

    async def __handle_embedding_pdf_request(self, request):
        body = PH.to_obj(json.loads(request.content), api_featherpdf_pb.EmbeddingPdfRequest)
        pdf_path = await download_pdf_async(body.fileUrl, body.filename)
        contents = read_pdf_sync_v3(pdf_path)
        for index, content in enumerate(contents):
            res = await self.aclient.embeddings.create(input=content, model="text-embedding-ada-002")
            embeds = [record.embedding for record in res.data]
            upsert_index(embeds[0], content, body.indexName, f"{body.fileId}-{index}")

        content = "".join(contents);
        messages = [
            {
                'role': "user",
                "content": f"""
                    Summarize this abstract delimited by triple slashes in three bullet points less than 500 words in markdown mode.
                    Also you should highlight key concepts.
                    ///{content}///
                """
            }
        ]
        conspectus = ""
        async for data in self.ask_gpt4(messages):
            conspectus += data.content
        response = api_featherpdf_pb.EmbeddingPdfResponse()
        response.conspectus = conspectus
        yield self.__wrap_response(response, action=api_common_pb.Action.EMBEDDING_PDF_RESPONSE)

    async def __handle_embedding_query_text_request(self, request):
        body = PH.to_obj(json.loads(request.content), api_featherpdf_pb.QueryTextRequest)
        res = await self.aclient.embeddings.create(input=body.text, model="text-embedding-ada-002")
        embeds = [record.embedding for record in res.data]
        queryResult = query_index(embeds[0], body.indexName, body.fileId)
        messageContent = []
        for match in queryResult['matches']:
            metadata = match['metadata']
            content = metadata["content"]
            score = match["score"]
            logger.info(f"{body.text} {score} {content}")
            if (score <= 0.75):
                continue
            messageContent.append(content)
        if len(messageContent) == 0:
            data = api_chitchat_pb.ChitchatCommonResponse()
            data.role = "assistant"
            yield self.__wrap_response(data, api_common_pb.Action.EMBEDDING_QUERY_RESPONSE)
            data = api_chitchat_pb.ChitchatCommonResponse()
            data.content = "没有查找到答案"
            yield self.__wrap_response(data, api_common_pb.Action.EMBEDDING_QUERY_RESPONSE)
            data = api_chitchat_pb.ChitchatCommonResponse()
            data.finishReason = "stop"
            yield self.__wrap_response(data, api_common_pb.Action.EMBEDDING_QUERY_RESPONSE)
        else:
            messages = [
                {
                    'role': 'system',
                    'content': 'Use the following pieces of context (or previous conversaton if needed) to answer the users question in markdown format.',
                },
                # previous messages
                {
                    'role': "user",
                    "content": f"""CONTENT: {messageContent[0]} USER_INPUT: {body.text}"""
                },
            ]
            async for data in self.ask_gpt4(messages):
                yield self.__wrap_response(data, action=api_common_pb.Action.EMBEDDING_QUERY_RESPONSE)

    async def ask_gpt4(self, messages):
        response = await self.aclient.chat.completions.create(
            # model='gpt-3.5-turbo-16k',
            model='gpt-4-turbo-preview',
            messages=messages,
            stream=True
        )
        async for chunk in response:
            logger.info(f"opneai response: {chunk}")
            data = api_chitchat_pb.ChitchatCommonResponse()
            choice = chunk.choices[0]
            delta = choice.delta
            data.role = delta.role or ''
            data.content = delta.content or ''
            data.finishReason = choice.finish_reason or ''
            data.index = choice.index or 0
            data.model = chunk.model or ''
            yield data

    def __wrap_response(self, data, action):
        response = api_common_pb.Response()
        response.action = action
        response.content = json.dumps(PH.to_json(data));
        return response


if __name__ == "__main__":

    root_path = os.path.dirname(os.path.realpath(__file__))
    SysEnv.set(SysEnv.APPROOT, root_path)

    server = Server()
    asyncio.get_event_loop().run_until_complete(server.server)
    asyncio.get_event_loop().run_forever()
