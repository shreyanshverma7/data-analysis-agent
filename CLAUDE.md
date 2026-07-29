# CLAUDE.md — Data Analysis Agent

<!-- AI context file. Claude Code reads this first. Keep current — stale context produces wrong code. -->

## What this project is

**One-liner:** A multi-agent LangGraph pipeline that answers natural-language questions about any
tabular dataset (CSV/Excel/JSON) — an LLM plans and interprets, generated pandas/matplotlib runs in
an E2B sandbox, and the answer is grounded in the real computed output plus a chart.

**Category/Tier:** Portfolio / GitHub · **Tier 2 (Standard)**

**Current milestone:** **M4 — Generic agent, no dataset hardcoding** (= V5), and it is **blocked**.
See "Current state / gotchas" below before writing any code.

## Read these before coding

- `docs/02-PRD.md` — scope. **Must/Should/Won't is law.** Never implement Should/Won't items without an updated PRD.
- `docs/03-SYSTEM-DESIGN.md` — architecture, data model, API contracts. Follow them; propose changes in the doc first.
- `docs/04-CODE-PLAN.md` — current tasks + acceptance criteria. Work on exactly one task per session.
- `CODING_STANDARDS.md` — lint, structure, commit, and testing rules. Non-negotiable.

Also useful: `docs/00-INTAKE.md`, `docs/01-VALIDATION.md`, `docs/05-TEST-LAUNCH.md`,
`docs/06-ITERATE.md`. `AGENT_STEPS.md` is the **frozen** V1–V5 build log — read-only history, and
it is gitignored, so it exists only in the local working copy.

## Stack

| Layer | Choice | Why (vs. what alternative) |
|---|---|---|
| Frontend | Streamlit (`app.py`) | The only layer — no separate frontend. A single-user demo doesn't justify two deployables |
| Backend | None — the Streamlit process | LangGraph invoked in-process via `agent.run_agent()`; FastAPI + a queue was premature |
| Orchestration | LangGraph / LangChain | Explicit graph, parallel Send-API fan-out, typed state. Legibility is the point |
| Database | **None** | State in-memory per session; dataset carried as a CSV string in `AgentState`. See ADR-1 |
| Hosting | Docker + Render (free tier) | Migrated from Railway (Phase 34). Blueprint in `render.yaml`, health check `/_stcore/health` |
| Auth | None | No accounts, no stored data. Explicit Won't in the PRD |
| AI/LLM | Groq — Llama 4 Scout 17B primary, Llama 3.3 70B fallback, via LiteLLM (`config.get_llm()`) | Groq for free-tier throughput; Scout over 70B because one eval run exhausted 70B's daily cap. **⚠️ Both halves currently broken — see gotchas** |
| Code execution | E2B Code Interpreter | Generated code runs in an isolated sandbox — the grounding mechanism and the security boundary in one |
| Compute / viz | pandas + matplotlib | Executed inside the sandbox; charts returned by path |
| Observability | LangSmith | Per-node tracing; eval runs as named experiments |
| Evals | Custom harness (`evals/`) | Deterministic numeric checks + LLM-as-judge for completeness/clarity |

## Commands

```bash
# dev server:
streamlit run app.py

# CLI (debugging only):
python agent.py

# evals (needs GROQ_API_KEY + E2B_API_KEY; two passes):
python evals/eval.py --agent-pass --eval-set evals/titanic_eval_set.jsonl --dataset data/titanic.csv --limit 5
python evals/eval.py --judge-pass --eval-set evals/titanic_eval_set.jsonl --limit 5
python evals/ci_gate.py

# tests: NONE — no pytest suite exists. See docs/05-TEST-LAUNCH.md
# lint:  NONE — no ruff/mypy config, no pyproject.toml. Same open item
```

The missing test and lint commands are a **known, logged gap**, not an omission from this file.
`CODING_STANDARDS.md` requires unit tests on core logic at Tier 2 and this project has none. Do not
claim tests pass; if you add tests, add the `pyproject.toml` and `ruff` config in the same task.

## Working rules for AI sessions

1. One code-plan task per session; confirm the task ID before writing code.
2. Meet the task's acceptance criteria, write its tests in the same session.
3. Conventional commits referencing the task ID.
4. If the task reveals a design flaw: stop, update `03-SYSTEM-DESIGN.md`, then code.
5. Scope ideas mid-session → add to PRD scope-change log, do not implement.
6. Branch per task (`feat/<slug>`, `fix/<slug>`, `docs/<slug>`), PR even when self-merged — the PR
   is the review record.
7. Never claim a resilience mechanism works without a deliberate failure-injection test in the same
   PR. This project shipped a fallback that never fired for months; that rule exists because of it.

## Current state / gotchas

**⛔ The app is down. Read this first.**

- **Groq retired `meta-llama/llama-4-scout-17b-16e-instruct` (2026-07-29).** It is no longer served
  on the project's key. Every run — local, CI, and the live Render demo — fails. Fix is **M4.0** in
  `docs/04-CODE-PLAN.md` and it blocks the rest of M4.
- **The LiteLLM fallback has never worked.** `config.get_llm()` passes
  `fallbacks=[ChatLiteLLM(...)]`, but `ChatLiteLLM` defines no `fallbacks` field — the kwarg is
  silently absorbed. Prefer LangChain's `.with_fallbacks([...])`, and prove it fires before
  claiming it (M4.0.2).
- **`evals/judge.py:13` hardcodes the same dead model** via `ChatGroq`, duplicating model selection
  instead of importing from `config`. Fix it to read a `JUDGE_MODEL` constant (M4.0.3).

**Architecture notes that will bite otherwise:**

- `fan_out_node` is wired as a **conditional edge**, not a node, and it emits `Send` objects. It
  skips the viz specialist entirely when `df_schema` shows no numeric columns.
- `specialist_results` is the **only** reduced channel (`Annotated[list, operator.add]`). Every
  other state field is written by exactly one node — that invariant is what makes the parallel
  fan-out safe. Adding a second writer to any other field will produce
  `INVALID_CONCURRENT_GRAPH_UPDATE`.
- **Codegen nodes are deliberately not on structured output.** Groq's JSON mode rejects multi-line
  Python. This was tried and permanently reverted (Phase 23.4) — do not "fix" it.
- `nodes/analyst.py`, `codegen.py`, and `critic.py` are pre-V2 leftovers, unreachable from the
  current graph. `nodes/executor.py` **is** still used by both specialists.
- Type 2 sequential questions ("find the top-3 correlated features, then plot only those") are
  unsupported by design — specialists cannot pass intermediate results (ADR-3).
- Repo uses a **flat layout**, not `CODING_STANDARDS.md`'s `src/<package>/`. Accepted deviation,
  logged in the PRD scope-change log. Do not migrate it as a side effect of another task.
- Logging is `print`, not the `logging` module — a standards deviation, not yet scheduled.
- No `LICENSE` file and no repo topics — open item in `docs/05-TEST-LAUNCH.md`.
