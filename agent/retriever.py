import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    import chromadb
    from llama_index.core import VectorStoreIndex
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.core import Settings
except ImportError:
    print("WARNING: Missing required dependencies. To run this script, please install:")
    print("pip install llama-index llama-index-vector-stores-chroma chromadb pypdf llama-index-embeddings-openai")

def get_retriever():
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-large")
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(workspace_dir, "chroma_db")
    
    db = chromadb.PersistentClient(path=db_path)
    chroma_collection = db.get_or_create_collection("heritage_lens")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=Settings.embed_model,
    )
    return index

def retrieve_chunks(query: str, top_k: int = 15) -> list:
    """
    Query the vector DB and strictly extract text and the required metadata schema.
    """
    index = get_retriever()
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(query)
    
    results = []
    for node_with_score in nodes:
        node = node_with_score.node
        meta = node.metadata
        
        results.append({
            "text": node.text,
            "metadata": meta,
            "score": node_with_score.score
        })
    return results

if __name__ == "__main__":
    # Test execution
    chunks = retrieve_chunks("What was the ritual function of obsidian at Olmec ceremonial sites?")
    for c in chunks:
        print(c["metadata"])
