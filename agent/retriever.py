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
    Uses balanced retrieval across all source PDFs to prevent any single document
    from dominating the context.
    """
    index = get_retriever()
    
    # Detect all unique PDFs in the database
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        db_path = os.path.join(workspace_dir, "chroma_db")
        db = chromadb.PersistentClient(path=db_path)
        collection = db.get_collection("heritage_lens")
        
        # Get all metadatas to find unique source_names in the database
        results = collection.get(include=["metadatas"])
        source_names = set()
        for meta in results.get("metadatas", []):
            if meta and meta.get("source_name"):
                source_names.add(meta.get("source_name"))
        
        source_list = sorted(list(source_names))
    except Exception as e:
        print(f"Error fetching source names from database: {e}")
        source_list = []
        
    if len(source_list) <= 1:
        # Fallback to standard global query if only one or no PDFs are found in the DB
        print("Fallback to standard global retrieval.")
        retriever = index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query)
    else:
        # Balanced retrieval
        from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
        print(f"Balanced retrieval active across {len(source_list)} sources: {source_list}")
        
        # Determine number of chunks to fetch per source
        per_source_k = max(5, (top_k + len(source_list) - 1) // len(source_list))
        
        all_nodes = []
        for src_name in source_list:
            try:
                filters = MetadataFilters(
                    filters=[MetadataFilter(key="source_name", value=src_name)]
                )
                retriever = index.as_retriever(similarity_top_k=per_source_k, filters=filters)
                nodes = retriever.retrieve(query)
                all_nodes.extend(nodes)
            except Exception as e:
                print(f"Error retrieving from source {src_name}: {e}")
                
        # Sort merged nodes by score descending (handling None scores gracefully)
        nodes = sorted(all_nodes, key=lambda x: x.score if x.score is not None else 0.0, reverse=True)
        
    results = []
    # Deduplicate nodes by text to ensure uniqueness, keeping the highest score
    seen_texts = set()
    for node_with_score in nodes:
        node = node_with_score.node
        if node.text in seen_texts:
            continue
        seen_texts.add(node.text)
        
        # Apply similarity threshold of 0.22 to filter out unrelated chunks
        score = node_with_score.score
        if score is not None and score < 0.22:
            continue
            
        results.append({
            "text": node.text,
            "metadata": node.metadata,
            "score": score
        })
        if len(results) >= top_k:
            break
            
    return results

if __name__ == "__main__":
    # Test execution
    chunks = retrieve_chunks("What was the ritual function of obsidian at Olmec ceremonial sites?")
    for c in chunks:
        print(c["metadata"])
