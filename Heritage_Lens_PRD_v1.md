# Heritage Lens Agent — Product Requirements Document (PRD)
*Version 1.0 | 31 March 2026*
*Author: Ella (Nuvola) | Reviewer: J Lee*

---

## 1. OVERVIEW

### Product Name
Heritage Lens Agent

### One-Line Description
A domain-aware research agent that retrieves information from specialised archives and makes the construction of its answers visible and accountable.

### The Problem
Standard AI systems optimise for confident answers. When used for specialised research — cultural heritage, archaeology, legal archives, medical records — this creates a dangerous illusion of completeness. The system retrieves what it can find, generates a fluent answer, and hides everything it cannot confirm: missing sources, biased corpora, contested interpretations.

### The Solution
Heritage Lens Agent produces three-layer outputs. Every response shows not just *what* it found, but *where* it came from and *what it cannot tell you*. The system is designed to make knowledge construction visible rather than hiding it behind confident language.

### Hackathon Context
KXSB AR26 HackXelerator — Mission 4: Ethics, Agency & Societal Impact
Submission deadline: 10 April 2026

---

## 2. TARGET USERS

### Primary User (Demo Context)
**The Research Professional** — archaeologist, archivist, historian, or academic researcher who needs to query a specialised corpus and needs to trust the output enough to act on it.

Needs:
- Grounded answers tied to real sources
- Ability to assess the reliability of an answer
- Transparency about what the system does NOT know

### Secondary User (Hackathon Judges)
Non-technical and technical judges evaluating Mission 4 (Ethics & Agency) submissions. They need to understand the concept in under 90 seconds from looking at the screen.

---

## 3. CORE FEATURES

### Feature 1 — Research Query Input
**What it does:** User types a research question in natural language.
**Input:** Free text question
**Example input:** *"What was the ritual function of obsidian at Olmec ceremonial sites?"*
**Acceptance criteria:**
- Input box accepts free text
- Submit button triggers the agent pipeline
- Loading state visible while agent processes

---

### Feature 2 — Layer 1: The Grounded Answer
**What it does:** Returns a direct answer based only on retrieved sources.
**Output:** A paragraph of synthesised text
**Rules:**
- Uses ONLY retrieved context
- Any general knowledge used is explicitly labelled `[BACKGROUND — not retrieved]`
- If evidence is insufficient: states this explicitly rather than guessing
- Does NOT invent sources or citations

**Example output:**
> "Archaeological evidence from San Lorenzo and La Venta indicates obsidian was used in bloodletting rituals and as offerings at ceremonial centres. Blades found in elite burial contexts suggest a strong association with status and sacred practice. [BACKGROUND — not retrieved]: Obsidian's volcanic origin may have carried cosmological significance in Mesoamerican cultures broadly."

---

### Feature 3 — Layer 2: Source Grounding
**What it does:** Lists every source used to construct the Layer 1 answer.
**Output:** Structured list of sources

**Format:**
```
Source 1:
- Name: Ruta de la Obsidiana — Excavation Report 14
- Type: Excavation report
- Institution: UNAM / Museum of Anthropology

Source 2:
- Name: [Thesis title]
- Type: Academic thesis
- Institution: [University name]
```

**Rules:**
- Only sources present in retrieved context are listed
- If no valid sources retrieved: *"No reliable sources retrieved"*
- No invented citations under any circumstance

---

### Feature 4 — Layer 3: Epistemic Transparency Report
**What it does:** Critically analyses the answer just given — surfacing bias, gaps, and limits tied to the actual retrieved data.

**Output:** Structured four-part report

**Format:**
```
SOURCE BIAS:
- Dominant source types: [e.g. 4/5 Western academic papers]
- Institutional patterns: [e.g. UNAM, Italian university press]

ABSENCES:
- Missing knowledge types: [e.g. no indigenous oral traditions retrieved]
- Dataset gaps: [e.g. no community-held knowledge in corpus]

INTERPRETIVE LIMITS:
- [Specific to this query, e.g. "The term 'ritual function' reflects academic 
  categorisation and may not capture indigenous frameworks"]

CONFIDENCE: MEDIUM
- Justification: Material evidence well-documented but interpretive context 
  incomplete due to absence of community sources.
```

**Critical rules:**
- All claims must be tied to the actual retrieved sources — not generic disclaimers
- Generic statements ("some sources may be biased") are a failure state
- If retrieval is weak: expand Absences section, do NOT produce a confident answer

---

### Feature 5 — Judge Layer (Internal, not visible to user)
**What it does:** A second AI call that evaluates whether Layer 3 is specific and grounded or generic boilerplate.
**Output:** VALID or WEAK + two-sentence explanation
**Behaviour:** If WEAK → system regenerates Layer 3 before showing to user
**Visible to user:** No — this runs in the background

---

### Feature 6 — Failure Handling
**What it does:** When retrieval is insufficient, the system surfaces this explicitly rather than confabulating.

**Trigger:** Query returns weak or no relevant chunks

**Behaviour:**
- Layer 1 states: *"Retrieval is insufficient to answer this question definitively."*
- Layer 3 expands Absences section significantly
- System does NOT attempt to fill gaps with general knowledge

**Why this matters:** This is a feature, not a bug. For Mission 4 judges, how the system fails is as important as how it succeeds. The absence of evidence becomes the evidence.

---

## 4. USER FLOW

```
USER opens the app
    ↓
USER types a research question in the input box
    ↓
USER clicks "Submit" / presses Enter
    ↓
SYSTEM shows loading indicator
    ↓
AGENT retrieves top 3–5 chunks from corpus (with metadata)
    ↓
LLM generates 3-layer response
    ↓
JUDGE evaluates Layer 3 (VALID / WEAK)
    ↓
    [If WEAK] → LLM regenerates Layer 3
    ↓
SYSTEM displays 3-panel output:
    Panel 1: Layer 1 — Answer
    Panel 2: Layer 2 — Sources
    Panel 3: Layer 3 — Epistemic Transparency
    ↓
USER reads output
    ↓
USER can submit a new question (repeat from top)
```

---

## 5. UI REQUIREMENTS

### Layout
Three distinct panels displayed simultaneously after query submission:

| Panel | Content | Visual Priority |
|-------|---------|----------------|
| Panel 1 | Layer 1 — The Grounded Answer | Primary (largest) |
| Panel 2 | Layer 2 — Source Grounding | Secondary |
| Panel 3 | Layer 3 — Epistemic Transparency | Equal to Panel 1 — this is the differentiator |

### Design Principles
- Three panels must be visually distinct — different background colours or clear borders
- Panel 3 should be visually prominent, not an afterthought
- Clean, uncluttered — judges must grasp the concept in 10 seconds
- No technical jargon visible to the user (no mention of RAG, embeddings, vectors)
- Mobile responsiveness: not required for hackathon demo

### Input
- Single text input box at the top
- Clear submit button
- Loading state while processing

### Labels (user-facing language)
- Panel 1: **"The Answer"**
- Panel 2: **"Sources"**
- Panel 3: **"What This Answer Doesn't Know"** *(or "Transparency Report")*

---

## 6. CORPUS (DATA)

### Sources
- Ella's degree thesis — Mesoamerican cultural heritage / Ruta de la Obsidiana
- Professor's published book — same domain

### Metadata Schema (per chunk)
Each text chunk must carry:
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

### Why metadata matters
Layer 3 cannot function on raw text chunks. The agent needs to evaluate the *shape* of its sources — not just their content — to produce specific rather than generic transparency reports.

---

## 7. EXAMPLE INPUT / OUTPUT

### Query
*"What was the ritual function of obsidian at Olmec ceremonial sites?"*

### Expected Layer 1 Output
A 2–3 paragraph grounded answer about obsidian use in Olmec ceremonial contexts, citing specific sites and artefact types from the retrieved corpus.

### Expected Layer 2 Output
2–4 sources listed with name, type, and institutional origin.

### Expected Layer 3 Output
```
SOURCE BIAS:
- Dominant: 3/4 sources are Western academic publications
- Institutions: Italian university press, UNAM

ABSENCES:
- No indigenous oral traditions present in corpus
- No community-held knowledge about obsidian's spiritual significance
- No Nahua or Mixe-Zoque interpretive frameworks represented

INTERPRETIVE LIMITS:
- "Ritual function" is an academic categorisation that may not capture 
  indigenous understandings of obsidian use
- Corpus covers pre-2010 literature; more recent excavation data absent

CONFIDENCE: MEDIUM
- Material evidence well-documented; interpretive context incomplete
```

### Contingency Query (weak retrieval demo)
A query on a topic where the corpus has thin coverage — used to demonstrate failure handling as a feature.

---

## 8. OUT OF SCOPE (for this hackathon)

The following are explicitly NOT being built:
- User authentication or accounts
- Multi-language interface
- Mobile optimisation
- Document upload by end user
- Multi-agent swarm systems
- Real-time data ingestion
- Integration with external databases beyond the thesis/book corpus
- Persistent conversation history

---

## 9. TECHNICAL STACK SUMMARY

| Component | Decision |
|-----------|----------|
| LLM | GPT-4o (OpenAI API) |
| Embeddings | OpenAI text-embedding-3-large |
| RAG Pipeline | LlamaIndex (preferred) |
| Vector DB | Qdrant on Vultr |
| Agent Orchestration | openclaw-based (buzman) |
| Judge Layer | Second GPT-4o call |
| UI | Streamlit — 3-panel layout |
| Infra | Vultr compute credits |

---

## 10. TEAM & RESPONSIBILITIES

| Person | PRD Responsibility |
|--------|-------------------|
| Ella | Owns this PRD, corpus preparation, Layer 3 prompt design |
| buzman | Reviews technical sections, confirms stack, builds pipeline |
| J Lee | Reviews UI requirements, builds Figma prototype from Section 5 |
| Nikhilesh | Uses example inputs/outputs in Section 7 for QA testing |

---

## 11. MILESTONES

| Date | Milestone |
|------|-----------|
| 1 April | PRD shared with team, GitHub repo set up |
| 5 April | buzman back in London, team sync call |
| 7 April | Working pipeline (one query → 3-layer output) |
| 8 April | Streamlit UI connected to pipeline |
| 9 April | Demo rehearsal, failure case tested |
| 10 April | Submission deadline |

---

## 12. SUCCESS CRITERIA

The submission is successful if a judge can:
1. Understand what the product does within 10 seconds of seeing the screen
2. See a clear, grounded answer to a research question
3. See exactly which sources produced that answer
4. See what the system does NOT know — tied to specific retrieved data
5. Watch the system handle weak retrieval honestly rather than confabulating

---

*This document will be reviewed and refined with J Lee before April 5th.*
*Next version: PRD v1.1 after J Lee feedback call.*
