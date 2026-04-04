from agent.retriever import retrieve_chunks
from agent.generator import generate_response
from agent.judge import evaluate_layer_3

def run_pipeline(query: str, max_retries: int = 2) -> dict:
    """
    Orchestrates the entire sequence:
    1. Retrieve chunks & metadata
    2. Generate Response
    3. Evaluate Layer 3 string via Judge
    4. Regenerate with penalty feedback if evaluated as weak!
    """
    print(f"Retrieving chunks for query: '{query}'")
    try:
        chunks = retrieve_chunks(query)
        print(f"Retrieved {len(chunks)} chunks from ChromaDB.")
    except Exception as e:
        print(f"Retrieval error (likely db off or path issues): {e}")
        chunks = []
        
    rejection_feedback = None
    
    for attempt in range(max_retries):
        print(f"LLM Processing 3-Layer Response (Attempt {attempt+1}/{max_retries})...")
        payload = generate_response(query, chunks, rejection_feedback)
        
        layer_3 = payload.get("layer_3_transparency", "")
        
        print("Judge is evaluating Layer 3 Specificity...")
        is_valid, feedback = evaluate_layer_3(layer_3)
        
        if is_valid:
            print("-> Judge Evaluation: VALID. Output meets Mission 4 standards.")
            return payload
        else:
            # Regenerate logic simplified for this prototype version
            print(f"-> Judge Evaluation: WEAK. Boilerplate detected.\nFeedback: {feedback}")
            rejection_feedback = feedback
            # The loop continues to regenerate_response providing the judge's rejection feedback
            
    print("Maximum retries over. Yielding final generated state.")
    return payload
