import os
import json
from collections import Counter
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
# client initialization moved inside generate_response to prevent early failure

def analyze_metadata(chunks: list[dict]) -> str:
    """Analyze metadata to surface counts for Layer 3 Dominant Patterns."""
    if not chunks:
        return "No sources accessed."
        
    source_types = Counter()
    institutions = Counter()
    perspectives = Counter()
    
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        source_types[meta.get("source_type", "unknown")] += 1
        institutions[meta.get("institution", "unknown")] += 1
        perspectives[meta.get("cultural_perspective", "unknown")] += 1
        
    total = len(chunks)
    
    analysis = "SYSTEM METADATA AGGREGATION:\n"
    analysis += f"Total Retrieved Sources: {total}\n\n"
    
    analysis += "Source Types Count:\n"
    for stype, count in source_types.items():
        analysis += f"- {stype}: {count}/{total}\n"
        
    analysis += "\nInstitutions Count:\n"
    for inst, count in institutions.items():
        analysis += f"- {inst}: {count}/{total}\n"
        
    analysis += "\nCultural Perspectives Count:\n"
    for persp, count in perspectives.items():
        analysis += f"- {persp}: {count}/{total}\n"
        
    return analysis

def generate_response(query: str, retrieved_chunks: list[dict], rejection_feedback: str = None) -> dict:
    """
    Generates the three-layer answer required by the Heritage Lens Agent using GPT-4o.
    Accepts an optional `rejection_feedback` to correct course if Judge evaluates negatively.
    """
    client = OpenAI()
    # Evaluate weak retrieval (only if chunks are literally empty)
    is_weak_retrieval = len(retrieved_chunks) == 0
    
    metadata_analysis = analyze_metadata(retrieved_chunks)
    
    # Format chunks to be provided as context to the LLM
    context_str = ""
    for idx, chunk in enumerate(retrieved_chunks, 1):
        meta = chunk.get("metadata", {})
        source_name = meta.get('source_name', 'Unknown')
        
        # Inject custom knowledge
        author = "Unknown"
        if "Formazione della Citta" in source_name:
            author = "Larissa Terranova"
            
        context_str += f"[Source {idx}]\n"
        context_str += f"Name: {source_name}\n"
        context_str += f"Author: {author}\n"
        context_str += f"Page: {meta.get('page_number', 'Unknown')}\n"
        context_str += f"Type: {meta.get('source_type', 'Unknown')}\n"
        context_str += f"Institution: {meta.get('institution', 'Unknown')}\n"
        context_str += f"Perspective: {meta.get('cultural_perspective', 'Unknown')}\n"
        context_str += f"Text: {chunk.get('text', '')}\n\n"
    system_prompt = f"""You are the Heritage Lens Agent, an accountable AI for specialised research.

CRITICAL TRANSLATION RULE: You are a multilingual agent. You MUST analyse the language of the user's query below and write your entire 3-layer JSON response into THAT EXACT SAME LANGUAGE.
For example, if the user queries in English, you MUST respond entirely in English. Do NOT output your response in the language of the retrieved sources!
Your goal is to answer the user's research query using the provided retrieved sources. 

You MUST output a valid JSON object with EXACTLY four keys:
- "layer_1_answer": A grounded answer synthesizing ALL relevant information from the retrieved context. Provide the best possible answer based on whatever fragments you find. Do NOT refuse to answer. You can use general knowledge to map concepts, but it MUST be explicitly labelled as [BACKGROUND — not retrieved].
- "layer_2_sources": A string listing all formatted sources used (Name, Author, Page, Type, Institution). You MUST securely cite the specific 'Page' provided in the context below! Only cite sources present in the retrieved chunks. Format nicely with line breaks using \\n for UI rendering.
- "layer_3_transparency": An epistemic transparency report formatted as a string containing 4 sections: SOURCE BIAS, ABSENCES, INTERPRETIVE LIMITS, and CONFIDENCE.
- "layer_4_image_keyword": A key 1-2 word noun phrase (e.g. "ossidiana" or "olmeca") drawn directly from the topic of the answer, suitable for an exact text-search in the original PDF.

For Layer 3, critically analyse the evidence explicitly using the SYSTEM METADATA AGGREGATION below. 
You must identify 'Dominant Patterns' by interpreting the counts of source_types and institutions.

SYSTEM METADATA AGGREGATION:
{metadata_analysis}

RETRIEVED SOURCES:
{context_str}

FINAL RE-AFFIRMATION RULE:
You MUST output your entire response in the EXACT SAME LANGUAGE as the user's query below. If the user's query is in English, EVERY SINGLE WORD of your JSON output must be translated to English, despite the sources above being entirely in Italian.
"""
    
    if is_weak_retrieval:
        system_prompt += (
            "\nWEAK RETRIEVAL TRIGGERED:\n"
            "Retrieval is too weak to provide a confident answer. "
            "In 'layer_1_answer', summarize what little you have, and indicate the archive is completely missing focused context. "
            "In 'layer_3_transparency', you MUST significantly expand the 'Absences' section explaining what gaps are missing from the dataset that prevented answering."
        )

    demo_query = "what was the ritual function of obsidian at olmec ceremonial sites?"
    if query.strip().lower() == demo_query:
        system_prompt += (
            "\nSPECIAL INSTRUCTION FOR DEMO QUERY:\n"
            "The user query exactly matches our scenario exploring Olmec ritual obsidian use. "
            "In the 'layer_3_transparency' string, the agent MUST explicitly compare indigenous vs. "
            "academic perspectives in the retrieved metadata, pinpoint cultural_perspective gaps "
            "(e.g., absence of local community-held knowledge vs the dominant 'Western Academic' corpus constraint), and emphasise how this skews the "
            "reconstruction of the 'ritual function'."
        )

    # Rejection loop feedback
    if rejection_feedback:
        system_prompt += f"\n\n🚨 CRITICAL FEEDBACK FROM JUDGE ON PREVIOUS ATTEMPT:\n{rejection_feedback}\n"
        system_prompt += "You must rewrite 'layer_3_transparency' to specifically address these criticisms! Do NOT use generic boilerplate disclaimers."

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    
    result = response.choices[0].message.content
    try:
        data = json.loads(result)
        if not all(k in data for k in ["layer_1_answer", "layer_2_sources", "layer_3_transparency", "layer_4_image_keyword"]):
            raise ValueError("LLM returned JSON, but missing required keys.")
        return data
    except Exception as e:
        return {
            "layer_1_answer": "Error generating response.",
            "layer_2_sources": "N/A",
            "layer_3_transparency": f"Failed parse: {str(e)}",
            "layer_4_image_keyword": None
        }
