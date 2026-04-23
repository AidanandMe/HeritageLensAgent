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

        /* The Differentiator Panel needs to be the iconic "light blue" from the PRD, reinvented */
        .panel-blue {
            background: linear-gradient(135deg, #7DD3FC 0%, #38BDF8 100%);
            padding: 32px;
            border-radius: 20px;
            min-height: 550px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 10px 25px -5px rgba(14, 165, 233, 0.3), inset 0 2px 4px 0 rgba(255, 255, 255, 0.6);
            border: 1px solid #BAE6FD;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            animation: slideUpFade 0.6s ease-out forwards;
            opacity: 0;
            color: #082F49; /* Dark blue text for maximum contrast against cyan */
        }

        .panel-blue:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 25px -5px rgba(14, 165, 233, 0.5), inset 0 2px 4px 0 rgba(255, 255, 255, 0.8);
            filter: brightness(1.05);
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
            border-bottom: 2px solid rgba(8, 47, 73, 0.15);
            color: #0C4A6E;
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
            color: #0369A1; /* High contrast sky blue inside the light blue panel */
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
    </style>
    """, unsafe_allow_html=True)

    # Top Header
    st.markdown("""
    <div class="header-box">
        <h2>Heritage Lens Agent</h2>
        <p>KXSB AR26 — Mission 4</p>
    </div>
    """, unsafe_allow_html=True)

    # Search Bar Section
    col_input, col_button = st.columns([5, 1])
    with col_input:
        query = st.text_input("Ask a research question...", placeholder="[ Ask a research question in any language... ]", label_visibility="collapsed")
        st.caption("User types research question here and clicks Search")
    with col_button:
        # Provide vertical alignment with text input
        st.markdown("<div style='margin-top: 2px;'></div>", unsafe_allow_html=True)
        search_button = st.button("Search", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    import sys
    import os
    import importlib
    # Add root folder to sys.path to allow imports dynamically
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import agent.image_extractor
    import agent.generator
    import agent.retriever
    import agent.pipeline
    # Force python to clear out the old cached ghost modules
    importlib.reload(agent.image_extractor)
    importlib.reload(agent.generator)
    importlib.reload(agent.retriever)
    importlib.reload(agent.pipeline)
    from agent.pipeline import run_pipeline

    # Panels Setup
    c1, c2, c3 = st.columns(3)

    # Base UI State Placeholders
    ans_text = "[Text block — grounded answer based on retrieved sources]"
    src_text = "Submit a query to parse data sources..."
    transparency_text = "Submit a query to evaluate epistemic bounds..."

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

    # When the UI button is clicked!
    image_path = None
    if search_button and query:
        with st.spinner("Heritage Lens Agent is retrieving specialized sources and constructing the transparency report..."):
            try:
                result = run_pipeline(query)
                # LLM output uses \n, but raw HTML strings in st.markdown collapse those without <br> handling
                ans_text = result.get("layer_1_answer", "Error in Layer 1").replace('\n', '<br>')
                src_text = result.get("layer_2_sources", "Error in Layer 2").replace('\n', '<br>')
                
                trans_raw = result.get("layer_3_transparency", "Error in Layer 3").strip()
                for title in ['⚠️ SOURCE BIAS', '📄 ABSENCES', '🕵️ INTERPRETIVE LIMITS', '⚠️ CONFIDENCE']:
                    trans_raw = trans_raw.replace(f'**{title}**', title).replace(f'### {title}', title).replace(f'## {title}', title)

                titles = {
                    '⚠️ SOURCE BIAS': '#EF4444',
                    '📄 ABSENCES': '#F59E0B',
                    '🕵️ INTERPRETIVE LIMITS': '#0EA5E9',
                    '⚠️ CONFIDENCE': '#10B981'
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
                            
                transparency_text = rendered_html if rendered_html else trans_raw.replace('\n', '<br>')
                
                # Fetch image if a keyword was provided
                keyword = result.get("layer_4_image_keyword")
                if keyword:
                    from agent.image_extractor import extract_image_for_keyword
                    st.toast(f"Scanning academic corpus for visual data matching '{keyword}'...")
                    image_path = extract_image_for_keyword(keyword)
            except Exception as e:
                ans_text = f"Internal Error: {str(e)}"

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
    <h3>WHAT THIS ANSWER DOESN'T KNOW</h3>
    <div class="panel-content">
        {transparency_text}
    </div>
    <span class="layer-label">Layer 3: Epistemic transparency — tied to actual retrieved data</span>
</div>
""", unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class="footer-box">
        Heritage Lens Agent — Accountable AI for Specialised Research
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
