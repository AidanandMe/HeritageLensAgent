import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import streamlit as st
from dotenv import load_dotenv
import sys
import zipfile

workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(workspace_dir)

# If the database does not exist on the cloud server, rebuild it natively from the PDFs!
db_path = os.path.join(workspace_dir, "chroma_db")
sqlite_path = os.path.join(db_path, "chroma.sqlite3")

if not os.path.exists(sqlite_path):
    print("Cloud DB missing! Rebuilding natively from PDFs...")
    from agent.ingest import initialize_vector_db
    try:
        initialize_vector_db()
    except Exception as e:
        print(f"Ingestion failed: {e}")

load_dotenv(override=True)

def main():
    st.set_page_config(layout="wide", page_title="Heritage Lens Agent")

    # Initialize session state for persisting search results
    if "ans_text" not in st.session_state:
        st.session_state.ans_text = "[Text block — grounded answer based on retrieved sources]"
    if "src_text" not in st.session_state:
        st.session_state.src_text = "Submit a query to parse data sources..."
    if "transparency_text" not in st.session_state:
        st.session_state.transparency_text = "Submit a query to evaluate epistemic bounds..."
    if "trans_raw" not in st.session_state:
        st.session_state.trans_raw = ""
    if "image_path" not in st.session_state:
        st.session_state.image_path = None
    if "last_query" not in st.session_state:
        st.session_state.last_query = ""
    if "video_url" not in st.session_state:
        st.session_state.video_url = ""
    if "video_eval_report" not in st.session_state:
        st.session_state.video_eval_report = None
    if "video_title" not in st.session_state:
        st.session_state.video_title = ""

    import sys
    import os
    import importlib
    # Add root folder to sys.path to allow imports dynamically
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import agent.image_extractor
    import agent.generator
    import agent.retriever
    import agent.pipeline
    import agent.video_evaluator
    # Force python to clear out the old cached ghost modules
    importlib.reload(agent.image_extractor)
    importlib.reload(agent.generator)
    importlib.reload(agent.retriever)
    importlib.reload(agent.pipeline)
    importlib.reload(agent.video_evaluator)
    from agent.pipeline import run_pipeline

    # Custom CSS for styling the UI to match the wireframe
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

        /* Force standard streamlit elements to inherit standard typography */
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif !important;
            color: #F8FAFC;
        }

        /* Animated Dark Mesh Background on Streamlit root wrapper */
        [data-testid="stAppViewContainer"] {
            background-color: #020617; /* Slate 950 */
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(14, 165, 233, 0.1), transparent 25%),
                radial-gradient(circle at 85% 30%, rgba(139, 92, 246, 0.1), transparent 25%);
            color: #F8FAFC;
        }
        
        [data-testid="stHeader"] {
            background: rgba(2, 6, 23, 0.5) !important;
            backdrop-filter: blur(10px);
        }

        /* Hide Streamlit default UI elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        @keyframes slideUpFade {
            0% { opacity: 0; transform: translateY(30px) scale(0.98); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }

        /* Panel core design */
        .panel {
            background: rgba(30, 41, 59, 0.6);
            backdrop-filter: blur(16px);
            padding: 32px;
            border-radius: 20px;
            min-height: 550px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            animation: slideUpFade 0.6s ease-out forwards;
            opacity: 0;
            color: #E2E8F0;
        }
        
        /* Staggered entrance for panels 1, 2, 3 */
        div[data-testid="column"]:nth-of-type(1) .panel { animation-delay: 0.1s; }
        div[data-testid="column"]:nth-of-type(2) .panel { animation-delay: 0.2s; }
        div[data-testid="column"]:nth-of-type(3) .panel-blue { animation-delay: 0.3s; }

        .panel:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.15);
            background: rgba(30, 41, 59, 0.8);
        }

        /* The Differentiator Panel needs to be visually distinct but dark enough for text contrast */
        .panel-blue {
            background: linear-gradient(135deg, rgba(8, 47, 73, 0.85) 0%, rgba(12, 74, 110, 0.85) 100%);
            backdrop-filter: blur(16px);
            padding: 32px;
            border-radius: 20px;
            min-height: 550px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 10px 25px -5px rgba(14, 165, 233, 0.2), inset 0 1px 1px 0 rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(14, 165, 233, 0.3);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            animation: slideUpFade 0.6s ease-out forwards;
            opacity: 0;
            color: #E2E8F0;
        }

        .panel-blue:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 25px -5px rgba(14, 165, 233, 0.4), inset 0 1px 1px 0 rgba(255, 255, 255, 0.2);
            filter: brightness(1.1);
        }

        .panel-content {
            flex-grow: 1;
            font-size: 1.1rem;
            line-height: 1.7;
        }

        .header-box {
            background: rgba(15, 23, 42, 0.7);
            backdrop-filter: blur(20px);
            padding: 32px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.05);
            animation: slideUpFade 0.6s ease-out forwards;
        }

        .header-box h2 {
            margin: 0;
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(to right, #F8FAFC, #94A3B8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.025em;
        }

        .header-box p {
            margin: 0;
            color: #38BDF8;
            font-size: 1.1rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }

        .footer-box {
            text-align: center;
            margin-top: 60px;
            padding: 24px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            color: #64748B;
            font-weight: 400;
            letter-spacing: 0.05em;
        }

        h3 {
            font-size: 1.2rem;
            text-transform: uppercase;
            font-weight: 800;
            margin-top: 0;
            padding-bottom: 16px;
            margin-bottom: 24px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
            color: #F8FAFC;
            letter-spacing: 0.1em;
        }

        .panel-blue h3 {
            border-bottom: 2px solid rgba(14, 165, 233, 0.3);
            color: #E0F2FE;
        }

        .layer-label {
            font-size: 0.8rem;
            color: #94A3B8; /* Slate 400 for standard panels */
            margin-top: 32px;
            display: block;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 700;
        }

        .panel-blue .layer-label {
            color: #38BDF8; /* Sky 400 for dark background */
        }
        
        /* Streamlit inputs customization hack */
        div[data-testid="stTextInput"] input {
            border-radius: 16px !important;
            padding: 16px 24px !important;
            font-size: 1.2rem !important;
            background-color: rgba(30, 41, 59, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: white !important;
            box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.2) !important;
            transition: all 0.3s ease !important;
        }
        
        div[data-testid="stTextInput"] input:focus {
            border-color: #38BDF8 !important;
            box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.3), inset 0 2px 4px 0 rgba(0, 0, 0, 0.2) !important;
        }
        
        div[data-testid="stButton"] button {
            border-radius: 16px !important;
            font-weight: 800 !important;
            letter-spacing: 0.05em !important;
            min-height: 60px !important;
            background: linear-gradient(135deg, #0EA5E9 0%, #2563EB 100%) !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 4px 10px rgba(37, 99, 235, 0.4) !important;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        }
        
        div[data-testid="stButton"] button:hover {
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 8px 15px rgba(37, 99, 235, 0.6) !important;
        }

        div[data-testid="stButton"] button:disabled {
            background: rgba(255, 255, 255, 0.05) !important;
            color: rgba(255, 255, 255, 0.2) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            box-shadow: none !important;
            transform: none !important;
            cursor: not-allowed !important;
        }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("Research Context")
        st.markdown("**Target Corpus:** Heritage Lens Agent PDFs")
        
        # Diagnostic Check for Streamlit Cloud
        sqlite_check = os.path.join(workspace_dir, "chroma_db", "chroma.sqlite3")
        zip_check = os.path.join(workspace_dir, "chroma_db.zip")
        db_size = os.path.getsize(sqlite_check) / (1024*1024) if os.path.exists(sqlite_check) else 0
        zip_size = os.path.getsize(zip_check) / (1024*1024) if os.path.exists(zip_check) else 0
        st.caption(f"💾 *Diagnostics - DB: {db_size:.1f} MB | ZIP: {zip_size:.1f} MB*")

        st.markdown("---")
        st.write("This agent actively retrieves information from the curated corpus to ensure epistemic transparency.")

    # Top Header
    st.markdown("""
    <div class="header-box">
        <h2>Heritage Lens Agent</h2>
        <p>KXSB AR26 — Mission 4</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔍 Search Archive", "🎓 Video Evaluator"])
    with tab1:
        # Search Bar Section
        col_input, col_search, col_export = st.columns([4, 1, 1])
        with col_input:
            query = st.text_input("Ask a research question...", placeholder="[ Ask a research question in any language... ]", label_visibility="collapsed")
            st.caption("User types research question here and clicks Search")
        with col_search:
            # Provide vertical alignment with text input
            st.markdown("<div style='margin-top: 2px;'></div>", unsafe_allow_html=True)
            search_button = st.button("Search", use_container_width=True)
        with col_export:
            st.markdown("<div style='margin-top: 2px;'></div>", unsafe_allow_html=True)
            if st.session_state.last_query:
                export_ans = st.session_state.ans_text.replace('<br>', '\n')
                export_src = st.session_state.src_text.replace('<br>', '\n')
                export_trans = st.session_state.trans_raw
                
                export_md = f"""# Heritage Lens Agent — Research Session Export

**Query:** {st.session_state.last_query}

---

## 1. THE ANSWER
{export_ans}

---

## 2. SOURCES
{export_src}

---

## 3. WHAT THE SYSTEM DOESN'T KNOW (TRANSPARENCY REPORT)
{export_trans}

---
*Exported from Heritage Lens Agent — Accountable AI for Specialised Research*
"""
                st.download_button(
                    label="📥 Export Session",
                    data=export_md,
                    file_name=f"heritage_lens_{st.session_state.last_query.lower().replace(' ', '_')[:30]}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            else:
                st.button("📥 Export Session", disabled=True, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Panels Setup
        c1, c2, c3 = st.columns(3)

        # When the UI button is clicked! (Execute search first to update session state)
        if search_button and query:
            with st.spinner("Heritage Lens Agent is retrieving specialized sources and constructing the transparency report..."):
                try:
                    result = run_pipeline(query)
                    # LLM output uses \n, but raw HTML strings in st.markdown collapse those without <br> handling
                    local_ans = result.get("layer_1_answer", "Error in Layer 1").replace('\n', '<br>')
                    local_src = result.get("layer_2_sources", "Error in Layer 2").replace('\n', '<br>')
                    
                    trans_raw = result.get("layer_3_transparency", "Error in Layer 3").strip()
                    for title in ['⚠️ SOURCE BIAS', '📄 ABSENCES', '🕵️ INTERPRETIVE LIMITS', '⚠️ CONFIDENCE', '💡 FUTURE DEVELOPMENT']:
                        trans_raw = trans_raw.replace(f'**{title}**', title).replace(f'### {title}', title).replace(f'## {title}', title)

                    titles = {
                        '⚠️ SOURCE BIAS': '#EF4444',
                        '📄 ABSENCES': '#F59E0B',
                        '🕵️ INTERPRETIVE LIMITS': '#0EA5E9',
                        '⚠️ CONFIDENCE': '#10B981',
                        '💡 FUTURE DEVELOPMENT': '#8B5CF6'
                    }
                    
                    parts = []
                    current_title = None
                    current_content = []
                    
                    for line in trans_raw.split('\n'):
                        line_stripped = line.strip()
                        found_title = None
                        for t in titles.keys():
                            if line_stripped.startswith(t):
                                found_title = t
                                break
                        
                        if found_title:
                            if current_title:
                                parts.append((current_title, '\n'.join(current_content).strip()))
                            elif '\n'.join(current_content).strip():
                                parts.append((None, '\n'.join(current_content).strip()))
                            current_title = found_title
                            current_content = [line[len(found_title):].strip()]
                        else:
                            current_content.append(line)
                            
                    if current_title:
                        parts.append((current_title, '\n'.join(current_content).strip()))
                    elif '\n'.join(current_content).strip():
                        parts.append((None, '\n'.join(current_content).strip()))
                        
                    rendered_html = ""
                    for t, content in parts:
                        content_html = content.replace('\n', '<br>')
                        if t in titles:
                            color = titles[t]
                            rendered_html += f'<div style="border-left: 3px solid {color}; padding-left: 12px; margin-bottom: 20px;"><span style="color: {color}; font-weight: 800; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.05em;">{t}</span><br><br><span style="color: rgba(255,255,255,0.85); font-size: 0.95em;">{content_html}</span></div>'
                        else:
                            if content_html:
                                rendered_html += f'<p>{content_html}</p>'
                                
                    local_transparency = rendered_html if rendered_html else trans_raw.replace('\n', '<br>')
                    
                    # Fetch image if a keyword was provided
                    keyword = result.get("layer_4_image_keyword")
                    retrieved_chunks = result.get("retrieved_chunks", [])
                    local_image_path = None
                    if keyword:
                        from agent.image_extractor import extract_image_for_keyword
                        st.toast(f"Scanning academic corpus for visual data matching '{keyword}'...")
                        local_image_path = extract_image_for_keyword(keyword, retrieved_chunks)
                        
                    # Save to session state
                    st.session_state.ans_text = local_ans
                    st.session_state.src_text = local_src
                    st.session_state.trans_raw = trans_raw
                    st.session_state.transparency_text = local_transparency
                    st.session_state.image_path = local_image_path
                    st.session_state.last_query = query
                    
                    # Immediately rerun the script to update all components in-sync
                    if hasattr(st, "rerun"):
                        st.rerun()
                    else:
                        st.experimental_rerun()
                except Exception as e:
                    st.session_state.ans_text = f"Internal Error: {str(e)}"
                    st.session_state.src_text = "N/A"
                    st.session_state.transparency_text = "N/A"
                    st.session_state.trans_raw = ""
                    st.session_state.image_path = None
                    st.session_state.last_query = ""
                    
                    if hasattr(st, "rerun"):
                        st.rerun()
                    else:
                        st.experimental_rerun()

        # Pull variables from session state for rendering
        ans_text = st.session_state.ans_text
        src_text = st.session_state.src_text
        transparency_text = st.session_state.transparency_text
        image_path = st.session_state.image_path

        import base64
        def get_image_html(img_path):
            with open(img_path, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
            return f'<img src="data:image/png;base64,{data}" style="width:100%; border-radius:10px; margin-bottom:15px; border: 1px solid rgba(255,255,255,0.1);">'

        with c1:
            img_html = ""
            if image_path and os.path.exists(image_path):
                img_html = get_image_html(image_path)
                
            html_c1 = f'<div class="panel">\n<h3>THE ANSWER</h3>\n'
            if img_html:
                html_c1 += f'{img_html}\n'
                
            html_c1 += f'<div class="panel-content">\n<p>{ans_text}</p>\n</div>\n'
            html_c1 += '<span class="layer-label">Layer 1: Direct answer. Only retrieved content. General knowledge labelled [BACKGROUND]</span>\n</div>'
            
            st.markdown(html_c1, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
    <div class="panel">
        <h3>SOURCES</h3>
        <div class="panel-content">
            <p>{src_text}</p>
        </div>
        <span class="layer-label">Layer 2: Full attribution for every source used</span>
    </div>
    """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
    <div class="panel-blue">
        <h3>WHAT THE SYSTEM DOESN'T KNOW</h3>
        <div class="panel-content">
            {transparency_text}
        </div>
        <span class="layer-label">Layer 3: Epistemic transparency — tied to actual retrieved data</span>
    </div>
    """, unsafe_allow_html=True)

    with tab2:
        st.markdown("""
        <div class="header-box" style="background: linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%); margin-top: 15px; margin-bottom: 25px;">
            <h2>🎓 Academic Video Evaluator</h2>
            <p>Validate external video and YouTube content against verified Mesoamerican peer-reviewed sources</p>
        </div>
        """, unsafe_allow_html=True)
        
        col_v_input, col_v_btn = st.columns([4, 2])
        with col_v_input:
            video_url = st.text_input("YouTube Video URL", placeholder="Paste YouTube link here... (e.g. https://www.youtube.com/watch?v=...)", label_visibility="collapsed", key="eval_yt_url")
            st.caption("Paste a YouTube video link to extract its transcript and evaluate its claims.")
        with col_v_btn:
            st.markdown("<div style='margin-top: 2px;'></div>", unsafe_allow_html=True)
            eval_button = st.button("Evaluate Video / YouTube", use_container_width=True, key="eval_yt_btn")
            
        uploaded_video = st.file_uploader("Or upload a local video/audio file (Max 25MB)", type=["mp4", "mp3", "wav", "m4a"], key="eval_upload_file")
        
        if eval_button:
            target_source = video_url.strip() if video_url else ""
            if not target_source and not uploaded_video:
                st.warning("Please provide a YouTube URL or upload a local video file.")
            else:
                with st.spinner("Heritage Lens Agent is extracting transcript and compiling academic validation report..."):
                    try:
                        from agent.video_evaluator import extract_youtube_transcript, evaluate_video
                        
                        if target_source:
                            st.toast("Extracting transcript from YouTube...")
                            transcript_data = extract_youtube_transcript(target_source)
                            video_title = f"YouTube Video ({transcript_data['video_id']})"
                        else:
                            # Local video upload transcription
                            import tempfile
                            temp_dir = os.path.join(workspace_dir, "ui", "assets")
                            os.makedirs(temp_dir, exist_ok=True)
                            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_video.name)[1], dir=temp_dir) as tmp_file:
                                tmp_file.write(uploaded_video.read())
                                temp_path = tmp_file.name
                            
                            st.toast("Transcribing uploaded video file via Whisper...")
                            from openai import OpenAI
                            client = OpenAI()
                            with open(temp_path, "rb") as audio_file:
                                transcript_response = client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio_file,
                                    response_format="verbose_json"
                                )
                            transcript_data = {
                                "text": transcript_response.text
                            }
                            video_title = uploaded_video.name
                            
                            # Clean up temp file
                            try:
                                os.remove(temp_path)
                            except Exception:
                                pass
                                
                        st.toast("Analyzing claims against ground-truth archive...")
                        report = evaluate_video(transcript_data, video_title)
                        
                        # Save results to session state
                        st.session_state.video_url = target_source or video_title
                        st.session_state.video_eval_report = report
                        st.session_state.video_title = video_title
                        
                        st.success("Evaluation completed successfully!")
                        if hasattr(st, "rerun"):
                            st.rerun()
                        else:
                            st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Failed to run evaluation: {str(e)}")
                        
        if st.session_state.video_eval_report:
            report = st.session_state.video_eval_report
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f'<h3 style="color:#8B5CF6;">📊 Academic Validation Report: <i>{st.session_state.video_title}</i></h3>', unsafe_allow_html=True)
            
            # Show rating with color code
            rating = report.get("reliability_rating", "N/A")
            rating_color = "#10B981" if "high" in rating.lower() else ("#F59E0B" if "medium" in rating.lower() else "#EF4444")
            
            st.markdown(f"""
            <div style="background-color: rgba(30, 41, 59, 0.4); padding: 20px; border-radius: 16px; border-left: 5px solid {rating_color}; margin-bottom: 25px;">
                <h4 style="margin: 0 0 10px 0; color: {rating_color}; font-weight: 800; font-size: 1.15em;">ACADEMIC RELIABILITY RATING: {rating}</h4>
                <p style="margin: 0; color: rgba(255,255,255,0.85); font-size: 0.95em;">{report.get("summary", "No summary available.")}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show 3 columns: Corroborations, Discrepancies, Absences
            cv1, cv2, cv3 = st.columns(3)
            with cv1:
                html_cv1 = '<div class="panel" style="border-top: 3px solid #10B981;">\n<h3 style="color:#10B981;">✅ CORROBORATIONS</h3>\n<div class="panel-content">\n'
                for item in report.get("corroborations", []):
                    html_cv1 += f'<div style="margin-bottom:12px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:8px; color:rgba(255,255,255,0.85); font-size:0.95em;">• {item}</div>\n'
                if not report.get("corroborations", []):
                    html_cv1 += '<div style="color:rgba(255,255,255,0.5);">No direct corroborations identified.</div>\n'
                html_cv1 += '</div>\n<span class="layer-label">Claims supported by the local peer-reviewed books</span>\n</div>'
                st.markdown(html_cv1, unsafe_allow_html=True)
                
            with cv2:
                html_cv2 = '<div class="panel" style="border-top: 3px solid #F59E0B;">\n<h3 style="color:#F59E0B;">⚠️ DISCREPANCIES</h3>\n<div class="panel-content">\n'
                for item in report.get("discrepancies", []):
                    html_cv2 += f'<div style="margin-bottom:12px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:8px; color:rgba(255,255,255,0.85); font-size:0.95em;">• {item}</div>\n'
                if not report.get("discrepancies", []):
                    html_cv2 += '<div style="color:rgba(255,255,255,0.5);">No direct contradictions or discrepancies identified.</div>\n'
                html_cv2 += '</div>\n<span class="layer-label">Claims that differ or conflict with our database</span>\n</div>'
                st.markdown(html_cv2, unsafe_allow_html=True)
                
            with cv3:
                html_cv3 = '<div class="panel-blue" style="border-top: 3px solid #8B5CF6;">\n<h3 style="color:#8B5CF6;">🕵️ ABSENCES / SPECULATIONS</h3>\n<div class="panel-content">\n'
                for item in report.get("absences", []):
                    html_cv3 += f'<div style="margin-bottom:12px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:8px; color:rgba(255,255,255,0.85); font-size:0.95em;">• {item}</div>\n'
                if not report.get("absences", []):
                    html_cv3 += '<div style="color:rgba(255,255,255,0.5);">No unsupported speculative claims identified.</div>\n'
                html_cv3 += '</div>\n<span class="layer-label">Claims not present in our peer-reviewed sources</span>\n</div>'
                st.markdown(html_cv3, unsafe_allow_html=True)
                
            # Methodology details
            with st.expander("🔍 Show Evaluation Methodology"):
                st.markdown(f"**Queries generated to scan archive:** `{', '.join(report.get('queries_used', []))}`")
                st.markdown("**Verified database sources cited for validation:**")
                for src in report.get("sources_cited", []):
                    st.markdown(f"- *{src.get('source_name')}* (by {src.get('author')}, Page {src.get('page_number')})")

    # Footer
    st.markdown("""
    <div class="footer-box">
        Heritage Lens Agent - Accountable AI for Specialised Research
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
