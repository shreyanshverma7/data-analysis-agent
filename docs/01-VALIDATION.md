# 01 — Validation

> Stage 1. Exit gate: a verdict with reasons. A KILL here is a win. See PLAYBOOK.md → Stage 1.
> Depth: Tier 1 → section A only. Tier 2 → A+B. Tier 3 → all sections, with live web research.

> **Retroactive.** Written 2026-07-29 against a project that already shipped V1–V4 and is live.
> This documents the honest "why build it anyway", it does not gate work already done. Tier 2 →
> sections A + B are filled; section C is deliberately left blank per the depth rule above.

## A. Gut check (all tiers)

**Does something solve this already?**
1. **ChatGPT Code Interpreter / Advanced Data Analysis** — upload a CSV, ask in plain English, get
   computed answers and charts. Free tier, zero setup.
2. **PandasAI** — open-source library that puts a natural-language layer over a dataframe.
3. Notebook copilots generally (Colab AI, Cursor/Copilot in a `.ipynb`) for the same job done
   one-cell-at-a-time.

**If yes, why build anyway?** **For learning, and as portfolio proof.** The artifact *is* the
résumé evidence: a visible multi-agent architecture (parallel Send-API fan-out, structured
outputs, two-level retry, an eval framework, an eval-gated CI) that a technical reviewer can read
and assess. ChatGPT's version does the same job better for the end user and shows the reviewer
nothing. This is not a claim to beat the incumbents — it is a claim to have built the machinery.

**Will I actually finish this at my time budget?** Yes at the original scope (~10–12 hrs/week);
**no** at the scope it actually grew to. V1 was finishable and was finished. The honest answer,
with hindsight: the time budget was adequate and scope discipline was the binding constraint.
See the scope-creep note in `00-INTAKE.md`.

**Is the problem painful, frequent, and underserved?**
- Painful: **2/5** — writing ad-hoc pandas is tedious, not hard.
- Frequent: **4/5** — anyone working with tabular data hits this constantly.
- Underserved: **1/5** — thoroughly served, by free first-party tools.

Total 7/15. That is a weak product signal and a fine portfolio signal — the two are different
scores and this project only ever needed the second.

**Platform-risk / Jasper test (mandatory if AI-touching, any tier — P5):**
Fully exposed. OpenAI and Anthropic have *already* shipped the first-party "upload a CSV, ask
questions" flow with no setup; the next model release makes it better, cheaper, and more reliable
without this project getting a vote. None of the surviving answers apply: no proprietary data
(the user brings the file), no workflow depth (single-turn Q&A), no distribution, no network
effects, no regulatory moat.

**Honest verdict: no moat, and none intended.** This survives as a skill demonstration, not as a
product. That admission is carried forward explicitly into `02-PRD.md`'s Won't-list so nobody —
including future Shreyansh — mistakes it for a business idea later.

## B. Competitor scan (Tier 2+)

| Competitor | What it does well | Gap I'd exploit | Price |
|---|---|---|---|
| ChatGPT Data Analysis (Advanced Data Analysis) | Zero setup, huge context, handles messy files, conversational follow-ups | None on capability. Its architecture is invisible — it cannot serve as evidence of *how* such a system is built | Free tier / $20 mo Plus |
| PandasAI | Drop-in library, good DX for developers already in a notebook | Library, not a running system — no orchestration, no evals, no deployed demo to click | Open source (free) |
| Notebook copilots (Colab AI, Copilot in Jupyter) | Meets users where the work already happens | Cell-by-cell assistance, no end-to-end pipeline, no grounded-answer guarantee | Free / bundled |

**My differentiation in one sentence:** The differentiation is **legibility of engineering, not
end-user capability** — a reader can see the multi-agent graph, the retry policy, the structured
output contracts, and a CI gate that blocks merges on eval regression, none of which the
incumbents expose.

## C. Market & users (Tier 3 — use live web research)

*Not applicable — Tier 2 project. Section intentionally left blank per the depth rule at the top
of this doc. If this were ever reframed as a business idea, section C is the gate it would have to
pass first, and the Jasper test in section A is the reason to expect it wouldn't.*

## Verdict

- [x] **GO** — proceed to PRD at Tier **2**
- [ ] **PIVOT** — reshape and re-run intake: (what changes)
- [ ] **KILL** — reasons below; log in `graveyard.md`

**Reasoning (3–5 lines):**
GO at Tier 2, retroactively. The project is already built, already live, and already carries eval
evidence (1.00 numeric accuracy on Titanic, 0.90 on Wine Quality — see `06-ITERATE.md`), so this
verdict records a judgment rather than authorizing work.
It clears the Tier 2 bar it was actually built against — portfolio evidence — and fails the
product bar decisively on the Jasper test. Both are true simultaneously; the value of writing this
down is that the second half was true from day one and had never been stated.
Re-running validation "honestly" on a shipped, scored, deployed project would be theater. What is
not theater is the recorded admission of no moat, which now constrains the PRD.

---
*Next on GO: `02-PRD.md`.*
