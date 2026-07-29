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

**🟨 Hotfix M4.0 in progress — most of it landed, three subtasks remain.**

Groq retired `meta-llama/llama-4-scout-17b-16e-instruct` on 2026-07-29, taking down local, CI, and
the live Render demo. Root-caused as two separate bugs, both tracked under **M4.0** in
`docs/04-CODE-PLAN.md`:

- M4.0.1 ✅ — `config.py` repointed to `openai/gpt-oss-120b` primary; the dead `fallbacks=` kwarg
  on `ChatLiteLLM` (which defines no such field) replaced with a real
  `.with_fallbacks([...])` chain (PR #8).
- M4.0.2 ✅ — fallback proven to actually fire: forced `_PRIMARY_MODEL` to an invalid id, ran one
  real `invoke()`, confirmed via `response_metadata.model` that `groq/llama-3.3-70b-versatile`
  answered, reverted the temporary change.
- M4.0.3 ✅ — `evals/judge.py:13`'s hardcoded dead model replaced; judge model now reads
  `JUDGE_MODEL` from `config.py` (PR #9).
- M4.0.4 ✅ — eval suite re-run against the repointed models, baseline scores updated (PR #10).
- M4.0.5–M4.0.7 ⬜ not started — README still needs its judge-model/stack-link/score-table sync,
  no startup guard exists yet for an unavailable model, and the live Render URL hasn't been
  re-verified end-to-end since the repoint.

Don't trust this snapshot past its own edit — cross-check `git log --all --oneline`, `git branch
-a`, and `gh pr list --state all` before assuming a subtask's state.

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
