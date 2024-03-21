from pinecone import Pinecone, Vector

host = "featherpdf-5prrw9g.svc.gcp-starter.pinecone.io"
pc = Pinecone(api_key="aa8a989c-e95a-4759-8e32-e2a63cee37e5")

def upsert_index(vectors, content, index_name, vector_id):
    # From here on, everything is identical to the REST-based client.
    index = pc.Index(index_name, host=host)
    index.upsert([{"id": vector_id, "values": vectors, "metadata": {"content": content}}], namespace="featherpdf")

def query_index(vector, index_name, vector_id):
    index = pc.Index(index_name, host=host)
    result = index.query(
        namespace="featherpdf",
        vector=vector,
        top_k=10,
        include_metadata=True,
        include_values=False,
    )
    return result
