# 05 — Test & Launch: Data Analysis Agent

> Stages 6–7. Exit gate: every Must-story verified, launch checklist for your category green. See PLAYBOOK.md → Stages 6–7.
> Tier 1: manual smoke test + "it's live/usable" — skip the rest.

> **Retroactive — already launched.** v0.1 shipped June 2026, v0.4 July 2026, live on Render since
> July 2026. Verification dates below are the dates the work actually landed, per the frozen
> `AGENT_STEPS.md`. Items that are genuinely done are checked; items that are not are left
> unchecked with the reason stated. Nothing here is checked to make the page look finished.

## Test plan

### Acceptance verification (all tiers)

Stories are the Must-set from `02-PRD.md`.

| Story | Acceptance criteria | Verified (date) | Notes |
|---|---|---|---|
| U1 — Multi-format upload | CSV, `.xlsx`, `.xls`, JSON parse and preview; format auto-detected from extension | ✅ 2026-06 | Phase 18.1. Extension-based dispatch in `app.py`; `_build_schema()` and all downstream nodes unchanged |
| U2 — Grounded numeric answer | The number traces to pandas executed in the E2B sandbox; numeric accuracy ≥0.80 on the eval set | ✅ 2026-06 | Numeric accuracy **1.00** on Titanic (15 q), **0.90** on Wine Quality (10 q). Checked deterministically — never scored by the judge |
| U3 — Chart alongside the answer | Chart renders inline; viz skipped (not failed) on non-numeric datasets | ✅ 2026-06 | Chart-correct 15/15 Titanic, 10/10 Wine. Adaptive skip added in Phase 19.1 |
| U4 — Parallel specialists | Stats and viz dispatch via Send and fan in; one failing degrades, both failing hard-stops with a clear message | ✅ 2026-06 | Phases 12–14. Fan-in via `Annotated[list, operator.add]`; `SpecialistOutput` added to fix `INVALID_CONCURRENT_GRAPH_UPDATE` |
| U5 — Self-recovery | codegen ×3 → re-plan ×1 before the specialist gives up | ✅ 2026-06 | Per-specialist counters in `SpecialistState`; retries never enter conversation history |
| U6 — Published eval score | Judge scores numeric (deterministic), completeness, clarity; published in the README | ✅ 2026-06 | Phase 16. Two-pass runner + LangSmith experiments; scores and badges in the README |
| U7 — Typed LLM outputs | Plan, critic, narrative, and synthesis calls use Pydantic via `.with_structured_output()` | ✅ 2026-06 | Phases 23–24. 5 call sites, 4 schemas. Codegen deliberately excluded — Groq JSON mode rejects multi-line Python |
| U8 — Merge gate | Actions runs the eval subset on every PR to `main`, blocks below threshold, posts a comment | ✅ 2026-06 | Phase 26. Green on both triggers at 28.3 — numeric 1.00, chart 5/5, comment posted |
| U9 — Any dataset, no hardcoding | No Titanic/Wine strings in source; eval ground-truth generated from schema introspection | ⬜ **Not started** | Should-item, = M4 in `04-CODE-PLAN.md`. Not claimed as shipped |

**⚠️ All ✅ rows above were verified before 2026-07-29 and are not currently reproducible.** Groq
retired the pinned model on that date; every run now fails. The verifications happened and the
scores were real, but the suite cannot be re-run until M4.0 lands. Re-verification is the explicit
gate on M4.0.4.

### Automated tests (Tier 2+)

- [ ] Unit tests on core logic pass
- [ ] (Tier 3) Integration tests on every API endpoint pass
- [ ] Lint + type checks green

**These are unmet, and this is a real open item — not a formality.**

1. **There is no pytest suite. There is no `tests/` directory.** `CODING_STANDARDS.md` requires
   unit tests on core logic at Tier 2, and this project has none. What exists instead is the
   `evals/` framework: 25 questions across two datasets scored end-to-end by an LLM judge plus
   deterministic numeric checks. That is a genuinely useful quality signal and it is **not a
   substitute** — it needs live API keys and paid model calls, it takes minutes, it is
   non-deterministic on two of its three dimensions, and it cannot test a function in isolation.
   Concretely untested: `fan_out_node`'s numeric-dtype branch, the retry counters, the
   partial-failure policy in `synthesizer.py`, `_build_schema()`, and the format-detection dispatch
   in `app.py` — all of which are pure logic, cheap to test, and currently guarded by nothing.
2. **No lint or type checking.** `ruff` is not configured; there is no `pyproject.toml`, so neither
   `ruff check`/`ruff format` nor `mypy` runs anywhere — not locally, not in CI. The only CI job is
   the eval gate.
3. **Integration tests: N/A** — Tier 2, and there is no HTTP API to integrate against (see
   `03-SYSTEM-DESIGN.md`).

Not scheduled into a milestone yet — Shreyansh's call whether this becomes M5 or gets accepted as
a permanent Tier-2 deviation. Recorded here so the decision is deliberate rather than accidental.

### Edge & failure pass (Tier 2+)

- [x] Empty states, bad input, network failure handled without crashes — empty-state hero when no
  file is loaded; malformed generated code caught by the retry loop; specialist failure degrades
  gracefully; `run_agent()` wraps `graph.invoke()` in a catch-all.
  **Caveat:** that catch-all swallows the exception and `print`s it. It is why the H1 model
  deprecation surfaced to users as an opaque failure rather than a legible one. Handled without
  crashing ≠ handled well; M4.0.6 addresses this.
- [x] Secrets absent from repo (`git log` spot check, `.env.example` current) — `.env` gitignored
  from the first commit; `.env.example` lists all five required keys; `render.yaml` marks secrets
  `sync: false`.

## Deploy checklist

- [x] Deployed to: **Render** (free tier, Docker runtime, blueprint in `render.yaml`) — migrated
  from Railway in Phase 34 when its free tier ended
- [x] Env vars set in host — `GROQ_API_KEY`, `E2B_API_KEY`, `LANGCHAIN_API_KEY` entered in the
  Render dashboard; also present as GitHub Actions secrets for the eval gate
- [x] Error monitoring or at least log access — Render logs + LangSmith per-node tracing
- [x] Rollback: previous deploy restorable — Render keeps prior deploys; `main` is always the
  deployed commit
- [ ] **Live service currently failing** — health check passes (Streamlit serves), but any question
  errors out on the deprecated Groq model. Blocked on M4.0.7.

## First-10-users plan (all categories — do things that don't scale, P13)

**Not applicable in the usual sense — and saying so is more honest than inventing a list.** The
beachhead in `02-PRD.md` is *technical reviewers evaluating the repo*, not users who adopt a tool.
There is no onboarding to over-deliver on and nobody to DM. The equivalent of "first 10 users" here
is the first 10 people who open the GitHub repo or click the demo link from a résumé or LinkedIn
profile.

- **Who they are:** recruiters and engineers reaching the repo from a job application, the résumé
  link, or the LinkedIn Projects section.
- **How they're reached:** the live demo URL on the résumé — which makes M4.0.7 the highest-value
  open task in the project. A dead link in front of a reviewer is worse than no link.
- **Manual over-delivery:** the README doing the work an onboarding call would — architecture
  diagram, published eval scores, screenshots, a one-command quickstart.

## Distribution execution (P14 — the channel chosen in validation)

- **Channel:** résumé / LinkedIn / portfolio site — direct placement, not a growth channel. No
  content, SEO, or community strategy exists, and none is planned; per `01-VALIDATION.md` this is a
  portfolio artifact, not a product seeking users.
- **First 3 concrete distribution actions:**
  1. Fix the live demo (M4.0) — every other action routes through that link.
  2. Add topics/tags and a license to the repo, and pin it on the GitHub profile (see below).
  3. Keep the demo URL current wherever it already appears — résumé, LinkedIn, one-pager PDF —
     noting the parked rename phase would change it.

## Launch checklist — by category

### Portfolio / GitHub
- [x] README: what/why, demo GIF or screenshots, quickstart, architecture summary — all present;
  Mermaid diagram, two screenshots (Streamlit UI + LangSmith trace), eval score table, known limits
- [ ] Repo pinned, topics/tags set, license added — **none of the three done.** Verified
  2026-07-29: no `LICENSE` file in the repo, and `gh repo view` returns `licenseInfo: null` and
  `repositoryTopics: null`. Without a license the code is technically all-rights-reserved, which
  undercuts a repo whose entire purpose is being read and evaluated. Cheapest open item here
- [x] Live demo link (if deployable) — `data-analysis-agent-qrj3.onrender.com`, in the README with
  a cold-start note. ⚠️ Currently returns an error on any question (M4.0)

### Work automation
*N/A — not this category.*

### Business
*N/A — not this category. Per `01-VALIDATION.md` this project has no moat and is not a business;
a landing page, announcement, and analytics would be theater.*

**Shipped on:** v0.1 June 2026 · v0.4 July 2026 · live on Render July 7, 2026

---
*Next: `06-ITERATE.md`, 2–4 weeks after ship.*
