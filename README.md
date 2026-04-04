# Heritage Lens Agent
> "Most AI systems optimise for answers. This one makes the construction of those answers visible and accountable."

**KXSB AR26 HackXelerator — Mission 4: Ethics, Agency & Societal Impact**

---

## What is this?

Heritage Lens Agent is a domain-aware research agent for specialised archives where provenance, gaps, and contested interpretations matter. Unlike standard RAG systems that optimise for confident answers, it makes the *construction* of those answers visible.

Every response contains exactly three layers:

| Layer | What it does |
|-------|-------------|
| **Layer 1 — Answer** | Grounded response using only retrieved sources. General knowledge explicitly labelled `[BACKGROUND — not retrieved]` |
| **Layer 2 — Source Grounding** | Full attribution: source name, type, institutional origin |
| **Layer 3 — Epistemic Transparency** | Source bias, knowledge absences, interpretive limits, confidence score — tied to actual retrieved data, not generic disclaimers |

---

## The core differentiator

Standard RAG hides uncertainty. Heritage Lens Agent surfaces it as structured information.

When retrieval is weak, the system says so explicitly and expands the absences section rather than confabulating. **Failure is a feature, not a bug.**

---

## Corpus

- Ella's degree thesis (Mesoamerican cultural heritage / Ruta de la Obsidiana)
- Professor's published book (same domain)
- Both metadata-rich: source type, institutional origin, language, cultural perspective all known

---

## Technical Stack

| Component | Tool |
|-----------|------|
| LLM | GPT-4o (OpenAI API) |
| Embeddings | TBD — Gemini / OpenAI |
| RAG Pipeline | LangChain or LlamaIndex |
| Vector DB | Qdrant on Vultr |
| Agent Orchestration | openclaw-based architecture |
| Judge Layer | Second GPT-4o call evaluating Layer 3 specificity |
| UI | Streamlit — 3-panel layout |
| Infra | Vultr compute credits |

---

## Metadata Schema

Each retrieved chunk must carry:

```json
{
  "source_name": "",
  "source_type": "thesis | book | excavation_report | paper | catalogue | oral_account",
  "institution": "",
  "date": "",
  "language_of_origin": "",
  "cultural_perspective": "western_academic | indigenous | institutional | community"
}
```

Layer 3 only works if metadata is injected into the retrieved context. Raw text chunks are insufficient.

---

## Minimal Viable Pipeline

```
User query
    → Retrieve top 3-5 chunks (with metadata)
    → GPT-4o generates 3-layer response
    → Judge evaluates Layer 3 (VALID / WEAK)
    → If WEAK → regenerate Layer 3
    → Display in Streamlit 3-panel UI
```

---

## Repo Structure

```
heritage-lens-agent/
├── README.md
├── prompts/
│   ├── system_prompt_v1.md
│   ├── query_wrapper.md
│   └── judge_prompt.md
├── data/
│   ├── corpus/          <- thesis + book chunks
│   └── metadata/        <- metadata schema + tagged sources
├── agent/
│   ├── retriever.py
│   ├── generator.py
│   └── judge.py
└── ui/
    └── app.py           <- Streamlit 3-panel UI
```

---

## Team

| Person | Role |
|--------|------|
| **Ella** | Project Lead — concept, epistemic layer, pitch |
| **buzman** | Lead Engineer — pipeline, infra, orchestration |
| **J Lee** | UI Design — Figma prototype, demo flow |
| **Nikhilesh** | QA & Docs — query testing, submission |

---

## Demo Query

> "What was the ritual function of obsidian at Olmec ceremonial sites?"

Contingency: a query where corpus coverage is thin, demonstrating failure handling as a feature.

---

## Submission Deadline

**April 10, 2026**
