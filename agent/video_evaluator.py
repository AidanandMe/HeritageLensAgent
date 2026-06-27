import os
import re
import json
from youtube_transcript_api import YouTubeTranscriptApi

def get_youtube_id(url: str) -> str:
    """Extract YouTube video ID from various YouTube URL patterns."""
    pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|embed/|v/|shorts/)|youtu\.be/)([\w-]+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    if len(url.strip()) == 11 and re.match(r'^[\w-]+$', url.strip()):
        return url.strip()
    return None

def extract_youtube_transcript(youtube_url: str) -> dict:
    """Fetch transcripts from YouTube URL using youtube-transcript-api."""
    video_id = get_youtube_id(youtube_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL. Please provide a valid YouTube link.")
        
    try:
        # Try retrieving standard transcripts (prioritizing Italian, Spanish, English)
        transcript_list = YouTubeTranscriptApi().fetch(video_id, languages=['it', 'es', 'en'])
        full_text = " ".join([seg.text for seg in transcript_list])
        
        segments_dict = [
            {"text": seg.text, "start": seg.start, "duration": seg.duration}
            for seg in transcript_list
        ]
        
        return {
            "text": full_text,
            "segments": segments_dict,
            "video_id": video_id
        }
    except Exception:
        # Fallback to any language available
        try:
            transcript_list_api = YouTubeTranscriptApi().list(video_id)
            for transcript in transcript_list_api:
                fetched = transcript.fetch()
                full_text = " ".join([seg.text for seg in fetched])
                
                segments_dict = [
                    {"text": seg.text, "start": seg.start, "duration": seg.duration}
                    for seg in fetched
                ]
                
                return {
                    "text": full_text,
                    "segments": segments_dict,
                    "video_id": video_id
                }
        except Exception as inner_e:
            raise ValueError(f"Could not retrieve transcript from YouTube video (ID: {video_id}). Error: {str(inner_e)}")

def extract_key_queries(transcript: str) -> list:
    """Use GPT-4o to extract 3-4 academic keywords/questions representing the main claims."""
    from openai import OpenAI
    client = OpenAI()
    
    prompt = f"""You are an academic researcher. Analyze the following transcript of a video and extract the top 3-4 distinct research queries or keyword search phrases (in Italian or Spanish if possible, since the reference library is in Italian/Spanish, otherwise in English) that represent the main archaeological, historical, or cultural claims made in this video.
Return ONLY a JSON object containing a "queries" key which is a list of strings.

TRANSCRIPT:
{transcript[:4000]}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("queries", [])
    except Exception as e:
        print(f"Error extracting queries: {e}")
        return ["Mesoamerica", "Olmec heads", "San Lorenzo"]

def evaluate_video(transcript_data: dict, video_title: str) -> dict:
    """Evaluate video claims against retrieved academic chunks from vector store."""
    from openai import OpenAI
    from agent.retriever import retrieve_chunks
    
    transcript_text = transcript_data["text"]
    
    # 1. Extract queries
    queries = extract_key_queries(transcript_text)
    
    # 2. Retrieve matching academic grounds
    all_chunks = []
    for q in queries:
        chunks = retrieve_chunks(q, top_k=4)
        all_chunks.extend(chunks)
        
    seen_texts = set()
    retrieved_chunks = []
    for c in all_chunks:
        txt = c.get("text", "")
        if txt not in seen_texts:
            seen_texts.add(txt)
            retrieved_chunks.append(c)
            
    # Format database sources
    context_str = ""
    for idx, chunk in enumerate(retrieved_chunks, 1):
        meta = chunk.get("metadata", {})
        source_name = meta.get("source_name", "Unknown")
        
        # Inject custom knowledge/author if missing
        author = meta.get("author", "Unknown")
        if "Formazione della Citta" in source_name:
            author = "Larissa Terranova"
        elif "Mesoamerica tra Segno e Significato" in source_name or "MESOAMERICA TRA SEGNO E SIGNIFICATO" in source_name:
            author = "Romolo Santoni"
            
        page = meta.get("page_number", "Unknown")
        context_str += f"[Source {idx}] {source_name} (by {author}, Page {page}):\n{chunk.get('text', '')}\n\n"
        
    # 3. Call GPT-4o to compile validation report
    client = OpenAI()
    system_prompt = f"""You are the Heritage Lens Academic Evaluator, a specialized accountability agent. Your task is to critically evaluate claims in the provided video transcript against the verified academic sources in our database.

Provide an academic evaluation report in JSON format with exactly the following keys:
- "corroborations": List of claims in the video that are supported by the retrieved sources, citing which sources support them.
- "discrepancies": List of claims in the video that conflict with or differ from the retrieved sources, explaining the academic difference.
- "absences": List of claims or topics in the video that are not mentioned in our sources, or are ungrounded speculations.
- "reliability_rating": A rating of "High", "Medium", or "Low" representing the video's academic reliability, with a 2-3 sentence justification.
- "summary": A brief 3-4 sentence overview of the evaluation.

All comments and responses must be written in the same language as the video title or user context if possible.

VERIFIED SOURCES FROM ARCHIVE:
{context_str}
"""
    user_content = f"VIDEO TITLE: {video_title}\n\nVIDEO TRANSCRIPT:\n{transcript_text[:10000]}"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        report = json.loads(response.choices[0].message.content)
        report["queries_used"] = queries
        
        cited = []
        for c in retrieved_chunks:
            s_name = c.get("metadata", {}).get("source_name", "Unknown")
            auth = "Larissa Terranova" if "Formazione della Citta" in s_name else ("Romolo Santoni" if "MESOAMERICA" in s_name or "Mesoamerica" in s_name else "Unknown")
            cited.append({
                "source_name": s_name,
                "author": auth,
                "page_number": c.get("metadata", {}).get("page_number", "Unknown")
            })
        report["sources_cited"] = cited
        return report
    except Exception as e:
        return {
            "corroborations": ["Error running evaluation."],
            "discrepancies": [],
            "absences": [str(e)],
            "reliability_rating": "N/A",
            "summary": "Failed to compile the report."
        }
