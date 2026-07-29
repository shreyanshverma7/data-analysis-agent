# 02 — PRD: Data Analysis Agent

> Stage 2. Exit gate: strict MVP cut done, success metric measurable. See PLAYBOOK.md → Stage 2.
> Tier 1: fill Problem, Must-haves, Won't-do, Success metric only (≤1 page).

> **Retroactive.** Written 2026-07-29. The Must-cut below is reconstructed from what V1–V4 actually
> shipped; the Should-list is the V5 work currently in flight. This is an honest record of the
> scope that emerged, not the scope that was planned up front — no PRD existed during the build,
> which is precisely the gap this document closes.

## Press release (Tier 3 — write this FIRST, Amazon Working Backwards, P7)

*Tier 2 — launch tweet only, per the shortcut in the template.*

**Launch tweet (all tiers):**

> Ask any CSV a question in plain English — parallel LLM agents compute real pandas stats, ground a
> narrative in them, and hand you a chart. Eval-gated on every PR.

## Problem statement

**Problem:** Getting an ad-hoc statistical answer out of a tabular dataset costs more in pandas and
matplotlib boilerplate than in thinking, for questions that will be asked once and never again.
LLMs can write that code, but a model that only *writes* the analysis can also hallucinate its
result. The gap worth closing is grounding: run the generated code, and answer from its real
output.

**Beachhead user (P8 — uncomfortably narrow):** Technical reviewers — recruiters, hiring managers,
and other engineers — evaluating Shreyansh's agentic-systems skill via his GitHub and portfolio.
Deliberately **not** end-user data analysts. Ten of these readers coming away convinced the
architecture is real is the visible dent; ten data analysts using it weekly is not the goal and
never was (see the Jasper test in `01-VALIDATION.md`).

**Why now / why me:** E2B-style sandboxed execution matured in 2025–26, which is what makes a
grounded answer possible rather than a plausible one. Why me: the project doubles as the training
ground for the LangGraph / evals / structured-output skill line it is meant to evidence.

## User stories

Format: *As a \<user\>, I want \<capability\> so that \<outcome\>.* Each Must-story needs acceptance criteria.

| # | Story | Priority | Acceptance criteria |
|---|---|---|---|
| U1 | As a reviewer, I want to upload a CSV, Excel, or JSON file so that I can try the agent on data I chose myself. | Must | All three formats parse and render a preview; format is auto-detected from the extension; a bad file surfaces a readable error, not a traceback. |
| U2 | As a reviewer, I want a plain-English question answered with a real computed number so that I can trust the answer isn't hallucinated. | Must | The number in the final answer traces to pandas output executed in the E2B sandbox; numeric accuracy ≥0.80 on the eval set. |
| U3 | As a reviewer, I want a chart alongside the answer so that the result is legible at a glance. | Must | Chart renders inline in the Streamlit UI for chart-appropriate questions; viz specialist is skipped (not failed) for non-numeric datasets. |
| U4 | As a reviewer, I want stats and visualization work to run concurrently so that latency stays reasonable. | Must | Stats and viz specialists dispatch via LangGraph's Send API and fan in; one specialist failing degrades gracefully, both failing hard-stops with a clear message. |
| U5 | As a reviewer, I want the agent to recover from its own bad code so that a single malformed generation doesn't kill the run. | Must | Two-level retry: codegen retried ×3, then re-plan ×1, before the specialist gives up. |
| U6 | As a reviewer, I want a published eval score so that quality is evidenced rather than claimed. | Must | LLM-as-judge framework scores numeric accuracy (deterministic), completeness, and clarity; scores published in the README. |
| U7 | As a maintainer, I want LLM node outputs to be typed so that parsing failures surface as validation errors, not silent garbage. | Must | Plan, critic, narrative, and synthesis LLM calls use Pydantic schemas via `.with_structured_output()`. |
| U8 | As a maintainer, I want a merge gate so that an eval regression can't land on `main`. | Must | GitHub Actions runs the eval subset on every PR to `main` and blocks merge below the threshold; posts a score summary as a PR comment. |
| U9 | As a reviewer, I want the agent to work on *any* dataset with no dataset-specific code so that "general-purpose" is demonstrably true. | Should | No Titanic/Wine strings anywhere in source; eval ground-truth generated from schema introspection at eval time. |
| U10 | As a data analyst, I want saved sessions, my own account, and a queryable history. | Won't (v0.1) | — |

## Scope — the strict MVP cut

**Must (v0.1 — ships in ≤3 milestones):**
- Multi-format upload — CSV, Excel (`.xlsx`/`.xls`), JSON — with schema preview
- Parallel stats and viz specialist agents dispatched via LangGraph's Send API, with adaptive
  fan-out that skips viz on non-numeric datasets
- Two-level retry: codegen ×3 → re-plan ×1
- LLM-as-judge eval framework scoring numeric accuracy (deterministic float check + tolerance),
  completeness, and clarity
- Structured Pydantic outputs on the plan, critic, narrative, and synthesis LLM calls
  (`AnalysisPlan`, `CriticVerdict`, `NarrativeOutput`, `SynthesisOutput` — 5 call sites across
  `nodes/specialists/stats.py`, `viz.py`, `nodes/narrative.py`, `nodes/synthesizer.py`). Codegen
  nodes are deliberately excluded: Groq's JSON mode cannot serialize multi-line Python
- LiteLLM provider abstraction with a declared Groq fallback chain
- CI eval gate blocking merge below the numeric-accuracy threshold
- Streamlit UI: dataset preview (head + describe), sidebar metadata, heuristic suggested
  questions, per-answer elapsed time and token estimate

> **Correction on the record:** an earlier internal note described structured outputs as covering
> "all six LLM nodes". The code has 5 `.with_structured_output()` call sites across 4 schemas, and
> the two codegen nodes are intentionally left on plain generation. The Must-item above states what
> is actually true.

**Should (v0.2 candidates — do NOT build in v0.1):**
- Remove all Titanic/Wine hardcoding from source, config, UI copy, and CI
- Synthetic eval generation — derive ground-truth from pandas via schema introspection instead of
  hand-written expected answers
- Palmer Penguins as the neutral reference dataset
- CI redesign around the generated eval set

*(These four are the current open milestone — M4 in `04-CODE-PLAN.md`.)*

**Won't (explicit non-goals — re-read when tempted):**
- Multi-user auth or accounts
- Persistent storage / database / session history
- Non-tabular data (PDF, images, free text)
- Natural-language-to-SQL against live databases
- **Anything that implies this is a hosted product rather than a portfolio artifact.** Per the
  Jasper test in `01-VALIDATION.md` this has no moat and is not meant to have one. Treating it as
  a business is the specific mistake this line exists to prevent.

> Rule: if Must can't ship in ≤3 milestones, cut Must — don't stretch milestones.

## Success metrics

**The one metric that matters (P9 — singular by design):**
**Numeric accuracy ≥0.80 on the CI eval gate, sustained on every merged PR.** This is already
enforced in `evals/ci_gate.py`; it had simply never been written down as *the* metric until now.

**Guardrail:** A reviewer gets from landing on the live demo to a correct answer with a chart in
under a minute (excluding Render free-tier cold start), and the eval gate never gets weakened to
make a PR pass.

## Assumptions & risks

| Assumption/risk | Impact | Mitigation |
|---|---|---|
| A single vendor-hosted open-weights model stays available at a fixed model ID | **Realized 2026-07-29** — Groq retired Llama 4 Scout, the live demo went down | Startup availability check + a fallback that is actually exercised — tracked as HOTFIX H1 in the frozen `AGENT_STEPS.md` |
| The declared LiteLLM fallback chain works | **Realized** — `ChatLiteLLM` has no `fallbacks` field; the kwarg was silently absorbed and the fallback never fired | Rule adopted: any resilience mechanism gets a deliberate failure-injection test in the same PR, or it isn't claimed in the README |
| Groq's JSON mode can carry structured output for every node | Partially false — it rejects multi-line Python in a codegen schema | Codegen nodes stay on plain generation; documented as a deliberate exclusion |
| Scope stays cut | Realized — V1→V5 accreted phases past the point of "done" | Should/Won't lists above are now law; mid-build ideas land in the scope-change log first |
| Free-tier daily token caps are sufficient for CI eval runs | A full 15-question run exhausted the 70B daily cap once | Eval gate runs a `--limit 5` subset; model choice weighs throughput, not just quality |
| Numeric answers are grounded, not hallucinated | Core value claim — if false the project has no point | Every number comes from sandbox-executed pandas; numeric accuracy checked deterministically, not by the judge |

## Scope-change log

> Every mid-build "great idea" lands here first, as Should/Won't. Code changes only after this table changes.

| Date | Change | Decision |
|---|---|---|
| 2026-07-29 | Standardize project on project-os docs (`docs/00`–`06`, `CODING_STANDARDS.md`, template `CLAUDE.md`); freeze `AGENT_STEPS.md` | **Accepted**, tracked as Phase 35 — this PR |
| 2026-07-29 | Flat repo layout (`nodes/`, `evals/`, root-level `state.py`/`config.py`/`graph.py`/`app.py`) deviates from `CODING_STANDARDS.md`'s `src/<package>/` default | **Accepted deviation** — Shreyansh's call. Project is small and stable; a layout migration would touch every import for no functional gain. Logged, not hidden. Revisit if the module count grows or the package is ever published |

---
*Next: `03-SYSTEM-DESIGN.md`.*
