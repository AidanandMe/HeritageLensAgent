import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(override=True)

try:
    import chromadb
    from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Document
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.core import Settings
except ImportError:
    print("WARNING: Missing required dependencies. To run this script, please install:")
    print("pip install llama-index llama-index-vector-stores-chroma chromadb pypdf llama-index-embeddings-openai")

# Set up the OpenAI embedding model explicitly as required by the PRD
try:
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-large")
except NameError:
    pass # Catching omission if imports failed above

# The non-negotiable metadata mapping for our specific corpora.
# This JSON projection maps directly to the Layer 3 logic inside 'agent/generator.py'
METADATA_MAPPING = {
    "Formazione della Citta in Mesoamerica.pdf": {
        "source_type": "thesis",
        "institution": "Italian University Press",
        "cultural_perspective": "western_academic",
        "language_of_origin": "italian"
    },
    "MESOAMERICA TRA SEGNO E SIGNIFICATO.pdf": {
        "source_type": "book",
        "institution": "Centro Studi Americanistici - Circolo Amerindiano",
        "cultural_perspective": "western_academic",
        "language_of_origin": "italian"
    }
}

DEFAULT_METADATA = {
    "source_type": "unknown",
    "institution": "unknown",
    "cultural_perspective": "unknown",
    "language_of_origin": "unknown"
}

def load_documents_with_metadata(data_dir: str):
    """
    Load PDFs and forcefully inject strict metadata JSON to every resulting LlamaIndex chunk.
    This fulfills the non-negotiable requirement for Layer 3 (Epistemic Transparency report).
    """
    directory = Path(data_dir)
    documents = []

    if not directory.exists() or not directory.is_dir():
        print(f"Data directory '{data_dir}' not found.")
        return documents

    for filepath in directory.glob("*.pdf"):
        filename = filepath.name
        # Provide exact metadata mapping, or default if novel PDF
        metadata_dict = METADATA_MAPPING.get(filename, DEFAULT_METADATA.copy())
        
        # Include source_name so our Layer 2 UI component can cite it comfortably
        metadata_dict["source_name"] = filename

        if "Formazione della Citta" in filename:
            metadata_dict["author"] = "Larissa Terranova"
        elif "Mesoamerica tra Segno e Significato" in filename or "MESOAMERICA TRA SEGNO E SIGNIFICATO" in filename:
            metadata_dict["author"] = "Romolo Santoni"

        print(f"Parsing '{filename}' and injecting dict: {metadata_dict}")
        
        from pypdf import PdfReader
        try:
            reader = PdfReader(str(filepath))
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if not text:
                    continue
                page_meta = metadata_dict.copy()
                page_meta["page_number"] = str(i + 1)
                
                doc = Document(text=text, metadata=page_meta)
                documents.append(doc)
        except Exception as e:
            print(f"Error parsing {filename} with pypdf: {e}")
            
    return documents

def initialize_vector_db():
    print("=== INITIALIZING CHROMA VECTOR DATABASE ===")
    
    # Store the db locally in the workspace
    # Resolve workspace dir dynamically from script path
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(workspace_dir, "chroma_db")
    
    print(f"Database persist location: {db_path}")
    
    db = chromadb.PersistentClient(path=db_path)
    chroma_collection = db.get_or_create_collection("heritage_lens")
    
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    print(f"Scanning for PDF corpora in workspace: {workspace_dir}")
    documents = load_documents_with_metadata(workspace_dir)
    
    if not documents:
        print("No documents found. Nothing to ingest.")
        return
        
    print(f"Successfully loaded {len(documents)} raw document pages/fragments.")
    print("Chunking documents (chunk_size=512, overlap=50) and embedding into Vector DB...")
    
    # Node splitting parameters to ensure chunks are granular enough for robust retrieval
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    nodes = splitter.get_nodes_from_documents(documents)
    
    print(f"Created {len(nodes)} discrete chunks. Generating embeddings...")
    
    # Generates text-embedding-3-large embeddings & stores them into Chroma via StorageContext
    index = VectorStoreIndex(
        nodes, 
        storage_context=storage_context,
        show_progress=True
    )
    
    print(f"=== SUCCESS! ===")
    print(f"Processed and ingested {len(nodes)} chunks into the VectorDB.")
    print("Each chunk is stamped with its target {source_type, institution, cultural_perspective, language_of_origin} JSON mapping.")

if __name__ == "__main__":
    initialize_vector_db()
