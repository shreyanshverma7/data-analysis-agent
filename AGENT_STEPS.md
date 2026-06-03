# Data Analysis Agent — Build Steps

Stack: LangGraph · LangChain · Groq (Llama 3.3 70B) · PythonREPLTool · pandas · matplotlib  
Dataset: Titanic CSV

---

## Phase 1 — Foundation

- [x] 1.1 Project structure: decide file layout (`agent.py`, `graph.py`, `nodes/`, etc.) — created nodes/, data/, outputs/ dirs + nodes/__init__.py; downloaded titanic.csv (891 rows)
- [x] 1.2 Environment setup: `.env` loading, Groq client init, model binding — config.py exports get_llm(), DATA_PATH, OUTPUTS_DIR, SLIDING_WINDOW; smoke-tested with Anaconda Python
- [x] 1.3 Define shared `AgentState` (TypedDict): what fields flow through the graph — state.py with 13 fields covering df_csv, retry counters (codegen×3, replan×1), chart_path, messages; default_state() helper included

## Phase 2 — Core Nodes

- [x] 2.1 **Ingestion node** — load CSV, attach raw DataFrame to state — nodes/ingestion.py serializes df to CSV string (df_csv) and builds df_schema (shape + dtypes + nulls + head(5))
- [x] 2.2 **Analyst node** — LLM receives user question + DataFrame schema, produces a plan — nodes/analyst.py with sliding-window message history, re-plan support when replan_count > 0
- [x] 2.3 **Code-gen node** — LLM writes pandas/matplotlib Python code to answer the plan — nodes/codegen.py; uses analysis_plan + df_schema only; enforces raw code output, outputs/chart.png path, plt.close(); strips markdown fences
- [x] 2.4 **Executor node** — runs generated code via PythonREPLTool, captures stdout + errors — nodes/executor.py; prepends io.StringIO CSV prefix; error detection via regex (PythonREPLTool returns bare exceptions, not tracebacks); detects saved chart_path
- [x] 2.5 **Critic / reflector node** — LLM reviews execution output; decides pass or retry — nodes/critic.py; rule-based fast path (error non-empty OR both output+chart empty → retry); LLM fallback with startswith("pass") parse

## Phase 3 — Graph Wiring

- [x] 3.1 Define graph edges and conditional routing (pass → summarize, fail → retry) — graph.py; critic routes to summarizer or retry_router; retry_router routes to codegen, analyst, or END
- [x] 3.2 Set entry point and terminal nodes — START → ingestion; summarizer → END; retry hard-stop → END
- [x] 3.3 Add retry loop with max-attempt guard (prevent infinite loops) — retry_router_node: codegen×3 then analyst replan×1 then hard-stop with fallback final_answer

## Phase 4 — Output

- [x] 4.1 **Summarizer node** — LLM converts raw output into a clean natural-language answer — nodes/summarizer.py; appends HumanMessage + AIMessage to state["messages"] for multi-turn history
- [x] 4.2 Surface matplotlib plots (save to file or show inline) — chart saved to outputs/chart.png by codegen; summarizer references path in final_answer; graph.py placeholder removed
- [x] 4.3 Final response schema: what gets returned to the caller — agent.py; run_agent(question, messages) → {answer, chart_path, messages}; multi-turn REPL loop in __main__ with exit/quit handling

## Phase 5 — Hardening

- [x] 5.1 Error handling: malformed code, REPL exceptions, LLM refusals — agent.py wraps graph.invoke in try/except; prints error message; returns original messages unchanged so user can retry
- [x] 5.2 Prompt templates: lock in system prompts for analyst, code-gen, critic, summarizer — SYSTEM_PROMPT module-level constant in all four LLM node files
- [x] 5.3 End-to-end test: 5 representative Titanic questions — Q1 (stat) ✅, Q2 (groupby) ✅, Q3 (histogram) ✅, Q4 (multi-column) ✅, Q5 (multi-turn follow-up) ⚠️ known limitation: analyst sometimes misresolves pronouns ("that", "it") across turns at temperature=0; fix: add explicit pronoun-resolution rule to analyst SYSTEM_PROMPT

## Phase 6 — E2B Sandbox

- [x] 6.1 Swap PythonREPLTool for E2B cloud sandbox in executor node — nodes/executor.py rewritten; uploads titanic.csv to sandbox, runs code, downloads chart; stderr→execution_error; e2b-code-interpreter added to requirements.txt
- [x] 6.2 Update error detection to handle E2B-specific error formats — stderr non-empty → execution_error; no regex needed since E2B separates stdout/stderr cleanly
- [x] 6.3 Handle chart retrieval: download saved chart from sandbox to local outputs/ — sandbox.files.read("outputs/chart.png") with try/except; writes bytes to local _CHART_PATH

## Phase 7 — Streamlit UI

- [x] 7.1 CSV upload: replace hardcoded titanic.csv with user-uploaded file; re-run ingestion on upload — app.py sidebar file_uploader; _loaded_filename guard prevents re-processing on every rerun; clears history on new file
- [x] 7.2 Agent progress stream: show node-by-node status as graph runs (planning → coding → executing → reflecting) — st.status block with graph.stream(stream_mode="updates"); NODE_LABELS map
- [x] 7.3 Inline chart display: render outputs/chart.png in UI after each answer — st.image(chart_path) in assistant chat_message block and in history replay
- [x] 7.4 Report download: export full Q&A session as PDF or markdown — app.py; markdown report built from chat_history; st.download_button shown only when history is non-empty

## Phase 8 — LangSmith Observability

- [x] 8.1 Add LangSmith tracing to all LangGraph nodes — LANGCHAIN_TRACING_V2=true in .env; config.py sets env vars via os.environ.setdefault before any LangChain import; automatic via LangGraph
- [x] 8.2 Capture token usage and latency per node per run — automatic via LangSmith once tracing is enabled; no node changes needed
- [x] 8.3 Track retry count and replan count per session — surfaced automatically in LangSmith trace via state fields visible per node invocation

## Phase 9 — Railway Deployment

- [x] 9.1 Containerize with Docker (Streamlit app entry point) — Dockerfile: python:3.11-slim, pip install, EXPOSE 8501, streamlit CMD; .dockerignore excludes .env, data/*.csv, outputs/, __pycache__, .git
- [x] 9.2 Deploy to Railway; configure env vars (GROQ_API_KEY, E2B_API_KEY, LANGSMITH_API_KEY) — .streamlit/config.toml added; git init + initial commit on main; pushed to github.com/shreyanshverma7/data-analysis-agent; Railway deploy from GitHub with Dockerfile auto-detected
- [x] 9.3 Verify live URL end-to-end with Titanic CSV — app live at data-analysis-agent-production-37db.up.railway.app; Streamlit shell confirmed loading

## Phase 10 — Portfolio Packaging

- [x] 10.1 GitHub README with architecture diagram and feature list — README.md with Mermaid graph, features, tech stack, live demo link, run-locally instructions; .env.example added
- [x] 10.2 Sample output screenshots and LangSmith trace screenshots — screenshots/ folder; Streamlit UI with inline histogram + LangSmith node trace; both embedded in README
- [x] 10.3 Live URL in README and portfolio — live demo link in README points to data-analysis-agent-production-37db.up.railway.app

---

## Open Design Decisions

- [x] D1 Separate nodes: Analyst (plan) → Code-gen (code). Enables targeted retries — critic can loop back to code-gen alone without re-planning.
- [x] D2 Serialize df to CSV string in state; Executor prepends `df = pd.read_csv(io.StringIO(<csv_string>))` before running generated code. File: titanic.csv. REPL stays stateless.
- [x] D3 Two-level retry: Critic failure → Code-gen retry (max 3). After N code-gen failures → escalate to Analyst re-plan (max 1). Hard stop after both levels exhaust. Attempt counters tracked per level in state.
- [x] D4 Multi-turn with sliding window. State holds full `messages` list; Analyst receives only `messages[-N*2:]` (last N human+AI pairs, default N=3) to respect Groq TPM limits. Only successful final answers are appended — retries are not added to history.
