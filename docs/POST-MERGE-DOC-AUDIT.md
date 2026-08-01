# Post-Merge Doc Audit — reusable prompt

Run this in the VS Code sidebar chat after every PR merges. Sidebar's role here is
strictly **audit only** — it checks docs against real git state and reports what's
stale, but never edits files. If something's stale, it hands back replacement text
for the Claude Code terminal to apply (with a diff review), same as any other change.

Swap the PR number(s) and one-line description each time; the rest stays fixed.

```
PR #<N> just merged: <one-line description of what it changed>. Don't edit any
files — audit only. Run git log origin/main --oneline -10 to confirm what's
actually merged. Then check, against that ground truth:
- CLAUDE.md's "Current state / gotchas" section
- docs/04-CODE-PLAN.md's relevant task row(s) and the Progress table
- docs/03-SYSTEM-DESIGN.md's stack table (only if this PR touched config/
  architecture)
- README.md (only if this PR touched user-facing features or the stack)

For each: is it accurate right now, or stale? If stale, give me the exact
replacement text — don't touch the file.
```

## Why this exists

Across M4.0.1–M4.0.4, `CLAUDE.md`, `docs/04-CODE-PLAN.md`, `docs/03-SYSTEM-DESIGN.md`,
and `README.md` all drifted out of sync with `main` at least once — each was caught
only by manually diffing against `git log`, not by any rule or check. This prompt
turns that manual habit into a fixed, repeatable step instead of a fresh judgment
call every time.

## Related, not redundant

`.github/workflows/docs-sync-check.yml` (added in #13) is a CI-level complement,
not a replacement: it only flags whether `CLAUDE.md` or `docs/04-CODE-PLAN.md`
changed *at all* alongside code changes. It can't tell whether the content is
actually accurate. This prompt catches the sneakier case — a doc was touched, but
the wording is still wrong, or one of the other docs got missed.

## Boundary: docs vs anything that executes

Pure-prose doc commits (`CLAUDE.md`, `docs/*.md`, `README.md`) can go directly to
`main` — no branch or PR required, per the exception agreed 2026-07-30. Still read
the diff before committing. Anything that *runs* — CI workflows, `config.py`, code
under `nodes/`/`evals/`/`graph.py` — keeps the full branch + PR + diff-review
discipline. This distinction exists because `docs-sync-check.yml` itself shipped
with a YAML syntax error that was only caught because it went through a branch and
a diff review before merging.
