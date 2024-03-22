import asyncio
from functools import partial

from constants.pinecone import HOST, FEATHERPDF_NAMESPACE
from submodules.utils.sys_env import SysEnv

from pinecone import Pinecone

pc = Pinecone(api_key=SysEnv.get("PICENOCE_API_KEY"))

async def upsert_index(vectors, content, index_name, vector_id):
    loop = asyncio.get_running_loop()
    index = pc.Index(index_name, host=HOST)
    func = partial(
        index.upsert, 
        [{"id": vector_id, "values": vectors, "metadata": {"content": content}}],
        namespace=FEATHERPDF_NAMESPACE
    )
    await loop.run_in_executor(None, func)

def query_index(vector, index_name, vector_id):
    index = pc.Index(index_name, host=HOST)
    result = index.query(
        namespace=FEATHERPDF_NAMESPACE,
        vector=vector,
        top_k=10,
        include_metadata=True,
        include_values=False,
    )
    return result
