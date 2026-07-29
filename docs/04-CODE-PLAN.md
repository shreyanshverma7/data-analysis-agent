# 04 — Code Plan: Data Analysis Agent

> Stage 4. Exit gate: every task is one Claude Code session — concrete, bounded, verifiable. See PLAYBOOK.md → Stage 4.
> Mirror milestones/tasks into GitHub milestones/issues when scaffolding the repo.

> **This is the live tracker.** As of 2026-07-29 `AGENT_STEPS.md` is frozen and kept only as the
> historical build log for V1–V5. All new planning happens in this file. M1–M3 below are a
> retroactive map of work already shipped; M4 is the open milestone, re-hosted here from
> `AGENT_STEPS.md` Phases 29–34 without rewriting the tasks.

## Folder structure

**Actual layout** (`main`, 2026-07-29):

```
data-analysis-agent/
├── CLAUDE.md                    # AI context file (project-os template)
├── CODING_STANDARDS.md          # global standards, copied in
├── README.md
├── AGENT_STEPS.md               # FROZEN historical log — gitignored, local only
├── docs/                        # these numbered docs
│   ├── 00-INTAKE.md … 06-ITERATE.md
├── app.py                       # Streamlit UI — the only entry point users touch
├── agent.py                     # run_agent() wrapper + a CLI loop
├── graph.py                     # LangGraph topology
├── state.py                     # AgentState / SpecialistState TypedDicts
├── schemas.py                   # Pydantic structured-output contracts
├── config.py                    # env loading, model selection, get_llm()
├── nodes/
│   ├── ingestion.py  fan_out.py  narrative.py  synthesizer.py  summarizer.py
│   ├── analyst.py  codegen.py  critic.py  executor.py       # pre-V2, still present
│   └── specialists/
│       └── stats.py  viz.py
├── evals/
│   ├── eval.py  judge.py  ci_gate.py  langsmith_eval.py
│   └── titanic_eval_set.jsonl  winequality_eval_set.jsonl
├── data/                        # titanic.csv, winequality-red.csv (removed in M4)
├── screenshots/
├── .github/workflows/eval.yml   # CI eval gate
├── Dockerfile  render.yaml  requirements.txt
└── .env.example
```

### Deviation from `CODING_STANDARDS.md` — logged, not hidden

The standard specifies a `src/<package>/` layout with a mirroring `tests/`. This project uses a
**flat layout**: packages at the root (`nodes/`, `evals/`) and single modules at the root
(`state.py`, `schemas.py`, `config.py`, `graph.py`, `app.py`, `agent.py`). There is no `tests/`
directory at all — see `05-TEST-LAUNCH.md`.

**Decision (Shreyansh, 2026-07-29): keep the flat layout, accept the deviation.** The project is
small, stable, and has no packaging story — it is deployed as a container, never installed as a
package. Migrating would rewrite every import across ~15 modules for zero functional gain. Logged
as a scope-change row in `02-PRD.md`. Revisit if the module count grows meaningfully or the code is
ever published to PyPI.

*(Note: there is a second, unrelated cleanup here — `nodes/analyst.py`, `codegen.py`, `critic.py`,
and `executor.py` are the pre-V2 sequential pipeline. `executor.py` is still used by both
specialists; the other three are only reachable through code paths V2 removed. Not scheduled;
recorded so it is not rediscovered as a surprise.)*

## Milestones (≤3 for v0.1 — the strict MVP rule)

> Retroactive labeling: the build ran as 34 numbered phases, not milestones. M1–M3 below group
> those phases after the fact. Original phase IDs are carried in each Task cell so any row can be
> traced back to the frozen `AGENT_STEPS.md`.

### M1: Walking skeleton ✅ *(Phases 1–2)*
*Goal: thinnest end-to-end slice — one request flows through every layer.*

| Task | Description | Acceptance criteria | Depends on |
|---|---|---|---|
| M1.1 *(1.1–1.3)* | Foundation — file layout, `.env` + Groq client init, `AgentState` TypedDict with retry counters and `default_state()` | Repo runs; `config.get_llm()` smoke-tested; state flows | — |
| M1.2 *(2.1–2.2)* | Ingestion node (CSV → `df_csv` string + `df_schema`) and analyst node (question + schema → plan, sliding-window history) | A question produces a plan grounded in the real schema | M1.1 |
| M1.3 *(2.3–2.5)* | Codegen, executor (`PythonREPLTool`), and hybrid rule-based + LLM critic | Generated pandas runs; critic returns pass/retry | M1.2 |

### M2: Core features ✅ *(Phases 3–20, 23–27 — V1 through V4)*
*Goal: all Must-stories functional.*

| Task | Description | Acceptance criteria | Depends on |
|---|---|---|---|
| M2.1 *(3.1–3.3)* | Graph wiring: conditional routing, entry/terminal nodes, retry loop with max-attempt guard | codegen ×3 → replan ×1 → hard stop; no infinite loops | M1.3 |
| M2.2 *(4.1–4.3)* | Summarizer node, chart surfacing, `run_agent()` response shape | `{answer, chart_path, messages}` returned to caller | M2.1 |
| M2.3 *(5.1–5.3)* | Hardening: error handling, locked system prompts, 5-question end-to-end pass | All 5 representative questions answered, incl. a multi-turn follow-up | M2.2 |
| M2.4 *(6.1–6.3)* | Swap `PythonREPLTool` → **E2B sandbox**; stderr-based error detection; chart download | Generated code executes in an isolated sandbox; chart retrieved | M2.3 |
| M2.5 *(7.1–7.4)* | Streamlit UI: upload, node-by-node progress stream, inline chart, markdown session report | A user can upload and converse entirely in the browser | M2.4 |
| M2.6 *(8.1–8.3)* | LangSmith tracing, per-node token/latency capture, retry-count visibility | Every node appears in a LangSmith trace | M2.5 |
| M2.7 *(11.1–11.3)* | **V2 state redesign** — `specialist_results` as `Annotated[list, operator.add]`, `SpecialistState` | Parallel writes to state merge without conflict | M2.6 |
| M2.8 *(12.1–12.4)* | Stats and viz specialist subgraphs, narrative node, `fan_out` coordinator as a conditional edge | Both specialists dispatch via `Send` and fan in | M2.7 |
| M2.9 *(13.1–14.3)* | Synthesizer node, graph rewiring to the parallel topology, partial-failure policy | One specialist failing degrades; both failing hard-stops cleanly | M2.8 |
| M2.10 *(15.1–15.3)* | UI for parallel execution — side-by-side specialist indicators, output expanders, updated report | Progress for both specialists visible live | M2.9 |
| M2.11 *(16.1–16.4)* | **Eval framework** — 15-question set, LLM-as-judge (`judge.py`), two-pass runner, LangSmith experiments | Numeric checked deterministically; completeness/clarity judged | M2.9 |
| M2.12 *(18.1)* | Multi-format upload — CSV, `.xlsx`, `.xls`, JSON with extension-based parsing | All four extensions load and preview | M2.10 |
| M2.13 *(19.1–19.3)* | Adaptive fan-out — skip viz on non-numeric datasets; synthesizer and UI guards for a missing viz entry | All-text dataset produces no wasted viz retries | M2.12 |
| M2.14 *(20.1)* | Prompt cleanup — remove the dead `overview_plan` block from both analyst messages | No empty-string interpolation in prompts | M2.13 |
| M2.15 *(23.1–23.4)* | `schemas.py` + structured critic. `CodegenOutput` attempted and **permanently reverted** — Groq JSON mode rejects multi-line Python | Critic returns a typed `CriticVerdict`; codegen stays plain-text, documented | M2.14 |
| M2.16 *(24.1–24.4)* | Structured outputs on analyst, narrative, and synthesizer nodes; full-pipeline smoke test | No `with_structured_output` parse errors end-to-end | M2.15 |
| M2.17 *(25.1–25.4)* | LiteLLM provider abstraction in `config.get_llm()` with a declared Groq fallback chain | ⚠️ **Marked done, was not.** `ChatLiteLLM` has no `fallbacks` field — see the H1 block below | M2.16 |
| M2.18 *(26.1–26.4)* | CI eval gate — `--limit` flag, `.github/workflows/eval.yml`, `evals/ci_gate.py`, PR score comment | PR to `main` blocks below 0.80 numeric; comment posted | M2.11, M2.16 |
| M2.19 *(27.1–27.4)* | UI polish — dataset preview, sidebar metadata, heuristic suggested questions, elapsed/token metrics, hero empty state | All four visible in the deployed app | M2.18 |

### M3: Ship-ready ✅ *(Phases 21–22, 28, 34)*
*Goal: tested, deployed, launch checklist green.*

| Task | Description | Acceptance criteria | Depends on |
|---|---|---|---|
| M3.1 *(9.1–9.3)* | Containerize (Docker) and first deploy (Railway) with env vars | Live URL serves the app end-to-end | M2.5 |
| M3.2 *(10.1–10.3)* | V1 portfolio packaging — README with Mermaid architecture, screenshots, LangSmith trace, live link | A reader can understand and run it from the README alone | M3.1 |
| M3.3 *(17.1–17.3)* | V2 packaging — V2 architecture diagram, eval results in README, known-limits section, redeploy | README reflects the parallel architecture; PR #2 merged | M2.11 |
| M3.4 *(21.1–21.3)* | **Second eval dataset** — parameterize eval paths, add UCI Wine Quality (1,599 rows), run full eval | Numeric 0.90 / completeness 0.84 / clarity 0.84 / chart 10-of-10 — generalization proven | M2.11 |
| M3.5 *(22.1–22.2)* | V3 packaging — multi-format + adaptive routing documented, wine row added to the eval table, redeploy | Live URL verified with a Wine Quality upload | M3.4 |
| M3.6 *(28.1–28.4)* | V4 packaging — README V4 section, eval badges, CI green on the PR, squash-merge and redeploy | Workflow green on both triggers; live URL serves the new UI | M2.19 |
| M3.7 *(34.1–34.5)* | **Railway → Render migration** — `PORT`-binding Dockerfile, `render.yaml` blueprint, service created, README updated, live verification | `data-analysis-agent-qrj3.onrender.com` healthy; auto-deploy on `main` confirmed | M3.6 |

### M4: Generic agent — no dataset hardcoding 🟨 *(open; = V5, ex-Phases 29–34.6)*
*Goal: prove the agent works on any tabular dataset by generating ground-truth from the dataset
itself at eval time, instead of pre-writing expected answers.*

> Rows below are re-hosted verbatim from `AGENT_STEPS.md` Phases 29–34; the original task ID is in
> each Task cell. They were already written at one-session granularity with a concrete file target,
> so they are not rewritten here.

#### ⛔ M4.0 — Blocking hotfix (carried over from `AGENT_STEPS.md` HOTFIX H1)

**The app is currently down.** Groq retired `meta-llama/llama-4-scout-17b-16e-instruct`; every run
— local, CI, and production — fails. H1 was diagnosed on 2026-07-29 but never executed, and it
lived only in a file that is now frozen and gitignored. It is carried here so it is not lost.
**Nothing else in M4 can be verified until this lands.**

| Task | Description | Acceptance criteria | Depends on |
|---|---|---|---|
| M4.0.1 *(H1.1)* | `config.py` — repoint models (`openai/gpt-oss-120b` primary, `groq/llama-3.3-70b-versatile` fallback) and replace the dead `fallbacks=` kwarg with LangChain's `.with_fallbacks([...])` | Primary model resolves; fallback is a real, verifiable mechanism | — |
| M4.0.2 *(H1.2)* | Prove the fallback fires — set a garbage primary model ID, run one query end-to-end, confirm it completes via the fallback, then revert | Query completes without raising, via the fallback path | M4.0.1 |
| M4.0.3 *(H1.3)* | `evals/judge.py:13` — same deprecated model, hardcoded via `ChatGroq`. Repoint it and have it read a `JUDGE_MODEL` constant from `config.py` (`openai/gpt-oss-20b`) | Judge runs; model selection lives in one file | M4.0.1 |
| M4.0.4 *(H1.4)* | Re-run the eval suite and compare to the recorded baseline (1.00 Titanic / 0.90 Wine). **Gate on the whole hotfix** — below 0.80 numeric means the model choice is wrong | New scores recorded; README updated if they moved | M4.0.3 |
| M4.0.5 *(H1.5)* | `README.md` — judge model (line 53), stack link (line 85), eval score table; stop claiming a fallback capability until M4.0.2 proves one | README matches reality | M4.0.4 |
| M4.0.6 *(H1.6)* | Startup guard — one cheap model-availability check at boot that fails with "model X is no longer served; available: [...]" instead of a raw LiteLLM traceback | Unavailable model produces a legible error in the UI | M4.0.1 |
| M4.0.7 *(H1.7)* | Deploy and verify the live Render URL end-to-end with one real query | Resume link works | M4.0.5, M4.0.6 |

#### M4 — V5 tasks

| Task | Description | Acceptance criteria | Depends on |
|---|---|---|---|
| M4.1 *(29.1)* | `nodes/executor.py` — rename `"titanic.csv"` → `"dataset.csv"` in the `sandbox.files.write(...)` call and the `pd.read_csv(...)` line in the `prefix` string | No dataset-specific filename in the executor; CSV still sourced from `state["df_csv"]` | M4.0 |
| M4.2 *(29.2)* | `nodes/ingestion.py` — remove the `config.DATA_PATH` fallback branch; empty `df_csv` returns a user-facing "No dataset uploaded" error instead | Ingestion never silently loads a hardcoded file | M4.0 |
| M4.3 *(29.3)* | `config.py` — delete `DATA_PATH`; drop the `pathlib.Path` import if unused | No hardcoded dataset path in config | M4.2 |
| M4.4 *(29.4)* | `app.py:133` — hero copy → "Eval-tested on reference datasets — numeric accuracy verified via CI on every PR." | No dataset names in UI copy | M4.0 |
| M4.5 *(29.5)* | `evals/ci_gate.py:26` — parameterize the summary header via a new `--dataset-name` arg (default `"reference"`); pass it from `eval.yml` | CI comment carries no dataset name in code | M4.0 |
| M4.6 *(29.6)* | Delete `data/titanic.csv`, `data/winequality-red.csv`, `evals/titanic_eval_set.jsonl`, `evals/winequality_eval_set.jsonl` | Repo carries no Kaggle-classic datasets | M4.11 |
| M4.7 *(30.1)* | Create `evals/generate_eval_set.py` — `--dataset` / `--output` args, format auto-detection matching `app.py`, JSONL output | Generator runs on csv/xlsx/json and writes JSONL | M4.0 |
| M4.8 *(30.2)* | Descriptive-stats questions — per numeric column (cap 4): `"What is the average {col}?"` with `expected_numbers` from `df[col].mean()`, `expected_chart: true`, category `descriptive_stats` | Entries generated with correct ground-truth | M4.7 |
| M4.9 *(30.3)* | Null-analysis questions — per column with nulls (cap 2): `"How many rows have missing values in {col}?"`, tolerance 0, `expected_chart: false`, category `edge_case` | Exact null counts as ground-truth | M4.7 |
| M4.10 *(30.4)* | Distribution questions — per low-cardinality categorical (`nunique() <= 20`, cap 2): `"What is the breakdown of {col}?"`, facts from `value_counts()`, category `visualization` | Chart-expecting entries generated | M4.7 |
| M4.11 *(30.5)* | Groupby questions — first valid (categorical ≤20 uniques × numeric) pair: `"What is the average {num} for each {cat}?"`, ground-truth = max group mean | Groupby entry with correct max-mean value | M4.7 |
| M4.12 *(30.6)* | Correlation question — if ≥3 numeric columns, top correlated pair via `df.corr().abs().unstack()`, tolerance 0.05, category `multiturn_style` | Correct pair and coefficient | M4.7 |
| M4.13 *(30.7)* | Centralize tolerance in `_tolerance(value) -> max(0.5, abs(value) * 0.02)`; use it in every numeric builder | One tolerance formula, no hand-tuned constants | M4.8, M4.11, M4.12 |
| M4.14 *(30.8)* | Minimum-question guard — fewer than 5 entries falls back to row-count and column-count questions | CI never runs on fewer than 5 questions | M4.13 |
| M4.15 *(30.9)* | Smoke-test the generator on two datasets (one numeric-heavy, one mixed); record datasets used and question counts | Generated questions inspected and sensible | M4.14 |
| M4.16 *(31.1)* | Choose the reference dataset — **Palmer Penguins** (344 rows; 3 numeric, 2 categorical, nulls in `sex`); save as `data/reference.csv` | Dataset covers every generator category | M4.15 |
| M4.17 *(31.2)* | Generate `evals/reference_eval_set.jsonl` from `data/reference.csv`; verify ≥8 entries across all categories; commit both | Eval set committed and inspected | M4.16 |
| M4.18 *(31.3)* | Full eval pass against the reference dataset (`--agent-pass` then `--judge-pass`); record all four scores. Target numeric ≥0.85 | Scores recorded; tolerances adjusted if below target | M4.17 |
| M4.19 *(32.1)* | `eval.yml` — point at `data/reference.csv` and `evals/reference_eval_set.jsonl`; keep `--limit 5` | CI runs the reference dataset | M4.17 |
| M4.20 *(32.2)* | `ci_gate.py` — replace `chart_correct < 4` with `chart_correct < int(total * 0.8)`; keep the 0.80 numeric threshold | Gate generalizes to any eval-set size | M4.5 |
| M4.21 *(32.3)* | `ci_gate.py` — add `--results-file <path>` so `eval.yml` passes the results file explicitly instead of globbing `results_*.json` | No filename-ordering dependency | M4.20 |
| M4.22 *(32.4)* | Verify CI green — push the branch, confirm the gate passes and the PR comment shows Penguins scores with no "Titanic" | Green run, correct comment | M4.19, M4.21 |
| M4.23 *(33.1)* | `README.md` — add a V5 section (no hardcoding, synthetic eval generation, neutral reference dataset); replace the Titanic and Wine rows with a single reference-dataset row | README reflects the generic agent | M4.18 |
| M4.24 *(33.2)* | README badges — replace `titanic-eval` and `wine-eval` with a single `reference-eval-{score}`; keep the CI badge | Badges match the current eval set | M4.18 |
| M4.25 *(33.3)* | Clear any seeded dataset or default-file reference from the deployment environment — the app must open to the empty upload state | Live app opens with no pre-loaded data | M4.2 |
| M4.26 *(33.4)* | Squash-merge V5 → `main`; verify auto-deploy, empty state, and one end-to-end Penguins question in production | Generic pipeline confirmed in production | M4.22, M4.23, M4.25 |
| M4.27 *(34.6)* | Delete the old Railway project — no dangling service, no leftover GitHub webhooks | Nothing left behind on Railway | — |

## Task rules

1. Each task = one Claude Code session. Paste its acceptance criteria into the session.
2. A task spilling past 2 sessions gets split here first — fix the plan, then the code.
3. Tests are written inside the feature task, not deferred.
4. Commit per task, conventional message, reference the task ID (`feat: add auth endpoint (M2.1)`).

## Progress

| Milestone | Status | Notes |
|---|---|---|
| M1 | ✅ | Walking skeleton — Phases 1–2, shipped June 2026 |
| M2 | ✅ | Core features — Phases 3–20, 23–27 (V1–V4). One row is a false positive: M2.17's LiteLLM fallback never worked, fixed under M4.0 |
| M3 | ✅ | Ship-ready — Phases 21–22, 28, 34.1–34.5. Live on Render since July 2026 |
| M4 | 🟨 | In progress. **Blocked by M4.0** — the pinned Groq model was deprecated 2026-07-29 and the live demo is down. V5 tasks (M4.1–M4.26) not started; M4.27 (Railway cleanup) open and independent |

---
*During build: scope temptations → PRD scope-change log. Next after M3: `05-TEST-LAUNCH.md`.*
