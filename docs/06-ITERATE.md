# 06 — Iterate or Archive: Data Analysis Agent

> Stage 8. Run 2–4 weeks post-ship. Exit gate: a decision, not a feeling. See PLAYBOOK.md → Stage 8.

> **Retroactive**, written 2026-07-29 — roughly three weeks after the Render deploy went live on
> July 7, 2026, which is inside the intended 2–4 week window.

## Metric check

**Primary metric target (from PRD):** Numeric accuracy **≥0.80** on the CI eval gate, sustained on
every merged PR.

**Actual:** **1.00** on Titanic (15 questions) and **0.90** on Wine Quality (10 questions).
Completeness 0.85 / 0.84, clarity 0.85 / 0.84, chart-correct 15-of-15 and 10-of-10. The CI subset
(`--limit 5`) has passed on every PR to `main` since Phase 26 — numeric 1.00, chart 5/5 at the last
recorded run.

**Guardrail held?** ☑ — with one caveat and one break.
- *Held:* the gate threshold was never lowered to make a PR pass, and the demo answers in well
  under a minute once the container is warm.
- *Caveat:* Render's free tier adds a 30–60 s cold start on the first visit, which is exactly the
  visit a reviewer makes. Documented in the README, accepted, and worth naming as a real cost.
- *Broken as of 2026-07-29:* the numbers above are no longer reproducible. Groq retired the pinned
  model; every run fails. The scores were real when recorded — they are not a current claim. Full
  diagnosis in `03-SYSTEM-DESIGN.md`; re-verification is the gate on M4.0.4 in `04-CODE-PLAN.md`.

## Feedback collected

| Source | Feedback | Theme |
|---|---|---|
| Eval framework (25 questions, 2 datasets) | Numeric answers are reliable; narrative quality trails accuracy (completeness/clarity ~0.85 vs numeric 1.00) | Grounding works; prose is the weaker half |
| Self-review, Phase 17 | Type 2 sequential questions ("find the top-3 correlated features, *then* plot only those") are unsupported — specialists can't pass intermediate results | Architectural limit of the parallel fan-out |
| Self-review, Phase 19 | All-text datasets burned three retries on a viz specialist that could never succeed | Fixed by adaptive fan-out |
| Self-review, Phase 23 | Groq JSON mode rejects multi-line Python, so codegen can't use structured output | Structured outputs fit classification/planning, not code generation |
| Prior repo review | Root-level screenshot cruft and stale branches | Repo hygiene |
| Production, 2026-07-29 | Vendor deprecated the pinned model; app down; the advertised fallback had never worked | Vendor-pinning risk + an untested resilience claim |

**Top 3 themes:**
1. **Grounding is the thing that works.** Deterministic numeric checks at 1.00/0.90 are the
   project's strongest evidence, and they come from the architecture choice (sandboxed execution)
   rather than from prompt quality.
2. **The parallel fan-out has a real ceiling.** Independent specialists cannot express dependent
   questions. Not a bug — a consequence of ADR-3, and the honest limit to state up front.
3. **Unverified resilience is worse than none.** A fallback chain that was documented, shipped, and
   never exercised read as robustness for months while providing zero protection, and it is
   precisely what failed when the vendor moved.

**Which subset is alive? (P15 — the Twitch question):**
The **eval harness**, not the agent. `evals/` — deterministic numeric ground-truth plus an
LLM-judge layer, wired into a merge-blocking CI gate — is the part with reuse value beyond this
repo, the part that makes every claim in the README checkable, and (per `00-INTAKE.md`) the
picks-and-shovels variant that was never seriously compared before committing. If any 10% of this
project deserves to become its own thing, it is that.

## Decision

- [x] **ITERATE** — write v0.2 PRD (back to `02-PRD.md`; Should-items compete with new feedback for the next Must-cut)
- [ ] **MAINTAIN** — works, used, no active development; fix-only mode
- [ ] **ARCHIVE** — retro below, README gets a status badge, move on guilt-free

**v0.2 is exactly V5** — generalization: strip all dataset hardcoding, generate eval ground-truth
from schema introspection, move to a neutral reference dataset (Palmer Penguins), redesign CI
around the generated set. Already scoped as the Should-list in `02-PRD.md` and tracked as M4 in
`04-CODE-PLAN.md`.

**Sequencing is not negotiable:** M4.0 (the H1 hotfix) lands first. Iterating on generalization
while the live demo returns a stack trace optimizes the wrong thing — the resume link failing in
front of a reviewer is the expensive outcome, not a Titanic string left in `executor.py`.

**A dissent worth recording:** ITERATE is the right call *given* that V5 is already scoped and half
the value is the vendor-resilience fix. But `00-INTAKE.md` names scope creep as this project's
actual failure mode, and V5 is the fifth consecutive version. The honest framing is that M4 is the
**last** milestone before MAINTAIN, not the next in an open series. If a V6 of *features* gets
proposed after this, that is the signal the retro below was written and ignored.

## Retro (5 lines, always — this is where PM learning compounds)

**What worked:** The parallel specialist architecture and the eval-gated CI. Fan-out via Send with
an `operator.add` fan-in was the right shape and never needed rework, and a merge gate that blocks
on numeric accuracy turned "it's accurate" from a claim into an enforced property — which is the
single most useful thing in the repo for its actual audience.

**What didn't:** No pytest suite — 25 LLM-judged eval questions were treated as a testing strategy,
and they are not one (`05-TEST-LAUNCH.md` lists what's untested). No lint or type checking either.
The LiteLLM fallback was shipped, documented, and never exercised, so it was decorative for months.
And repo hygiene slipped — root-level screenshots, stale branches, still no `LICENSE`.

**What surprised me:** Groq's JSON mode rejecting multi-line Python in `CodegenOutput` (Phase 23.4)
— structured outputs suit classification and planning, not code generation, which was not obvious
going in. The bigger surprise was the second-order one: `ChatLiteLLM` silently swallowing a
`fallbacks=` kwarg it does not define. No error, no warning, no fallback — just a capability that
existed only in the README.

**Estimate vs. reality (time, scope):** Scope roughly tripled. V1 was the plan; V2–V4 shipped
anyway, and V5 is scoped on top. Each addition was individually defensible and the aggregate was
never re-decided — the project was demo-ready at V2 and kept accreting phases. Time per version
stayed roughly accurate; the count of versions did not.

**One thing I'll do differently next project:** Run intake and validation **before the first
commit**, not four versions later. Writing `01-VALIDATION.md` for this project produced one true
and useful sentence — *no moat, not meant to have one* — that was true from day one and would have
capped scope at V2 had it been written then. Corollary, from H1: any resilience mechanism gets a
deliberate failure-injection test in the same PR that adds it, or it does not get claimed in the
README.

---
*If iterating: v0.2 scope obeys the same strict MVP rule.*
