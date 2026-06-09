# Data Analysis Agent

A multi-agent LangGraph pipeline that answers natural-language questions about CSV data using Groq (Llama 3.3 70B) and executes code in E2B cloud sandboxes.

---

## Features

- Multi-turn conversation with sliding-window memory
- LLM-generated pandas + matplotlib code executed in isolated E2B sandboxes
- Two-level retry loop (code-gen × 3 → re-plan × 1)
- Hybrid rule-based + LLM critic
- Inline chart display
- Session report download
- LangSmith tracing for every node

---

## V2 Features

- **Parallel specialist agents** — Stats and Viz agents run concurrently via LangGraph's Send API, reducing total latency
- **Hybrid execution model** — Narrative agent runs sequentially after stats, grounding its interpretation in real computed numbers (zero hallucination risk)
- **LLM-as-judge eval framework** — 15-question eval dataset with deterministic numeric checks + LLM semantic scoring across three dimensions: numeric accuracy, completeness, clarity
- **LangSmith experiment tracking** — Eval results stored as named experiments, visible alongside trace data
- **Graceful partial failure** — Single specialist failure degrades gracefully; both computation agents failing triggers a hard stop with a clear error message

---

## V3 Features

- **Multi-format upload** — Accepts CSV, Excel (`.xlsx`, `.xls`), and JSON in addition to CSV
- **Adaptive routing** — Fan-out inspects the dataset schema; viz specialist is skipped for non-numeric datasets, avoiding wasted retries
- **Generalization proven on two datasets** — Evaluated on Titanic (891 rows) and UCI Red Wine Quality (1,599 rows, 12 numeric columns)

---

## Eval Results

Evaluated on two datasets using a hybrid framework — deterministic numeric checks + LLM-as-judge semantic scoring (`llama-4-scout-17b`).

| Dataset | Questions | Numeric accuracy | Completeness | Clarity | Chart correct |
|---|---|---|---|---|---|
| Titanic (V2) | 15 | 1.00 | 0.85 | 0.85 | 15/15 |
| Wine Quality (V3) | 10 | 0.90 | 0.84 | 0.84 | 10/10 |

> Numeric accuracy is checked deterministically (float parsing + tolerance). Completeness and clarity are scored by an LLM judge.

---

## Architecture

```mermaid
graph TD
    A([User Question]) --> B[Ingestion]
    B --> C[Fan-out Coordinator]
    C -->|Send| D[Stats Subgraph\ncodegen → executor → critic]
    C -->|Send| E[Viz Subgraph\ncodegen → executor → critic]
    D -->|fan-in| F[Narrative Node\nLLM-only, grounded in stats]
    E -->|fan-in| F
    F --> G[Synthesizer]
    G --> H[Summarizer]
    H --> I([Final Answer + Chart])
```

---

## Tech Stack

- [LangGraph](https://github.com/langchain-ai/langgraph)
- [LangChain](https://github.com/langchain-ai/langchain)
- [Groq / Llama 3.3 70B](https://groq.com)
- [E2B Code Interpreter](https://e2b.dev)
- [Streamlit](https://streamlit.io)
- pandas, matplotlib
- [LangSmith](https://smith.langchain.com)
- Docker, Railway

---

## Live Demo

**[data-analysis-agent-production-37db.up.railway.app](https://data-analysis-agent-production-37db.up.railway.app)**

---

## Run Locally

```bash
git clone https://github.com/shreyanshverma7/data-analysis-agent
cd data-analysis-agent
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
streamlit run app.py
```

**Required environment variables** (`.env`):

```
GROQ_API_KEY=
E2B_API_KEY=
LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=data-analysis-agent
```

---

## Screenshots

**Streamlit UI — inline chart answer**
![Streamlit UI](screenshots/streamlit-ui.png)

**LangSmith trace — node-by-node breakdown**
![LangSmith trace](screenshots/langsmith-trace.png)

---

## Known Limits

- **Type 2 sequential questions** — Questions where the visualization depends on specific intermediate results from the stats agent (e.g. "find the 3 most correlated features, then plot only those") are not supported. Both agents start from the same input and cannot pass intermediate results to each other. Standard filter-then-compute questions ("show survival rate for passengers over 60") work correctly as each agent independently applies the full computation.
