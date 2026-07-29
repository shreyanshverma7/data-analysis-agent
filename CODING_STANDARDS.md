# Coding Standards (Global — copy into every project)

Applies to the default stack: **Python backend + JS/TS frontend**. Adjust the tool names if a project deviates; the principles don't change.

## Repository

- One repo per project. `main` is always deployable/runnable.
- Branching: trunk-based for solo work — short-lived branches `feat/<slug>`, `fix/<slug>`, merged via PR (even self-merged; the PR is the review record and portfolio evidence).
- Commits: [Conventional Commits](https://www.conventionalcommits.org) — `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`. One logical change per commit.
- Never commit: secrets, `.env`, large data files, `node_modules`, `__pycache__`, virtualenvs. `.gitignore` from day one.
- Secrets live in `.env` (gitignored) with a committed `.env.example` listing required keys.

## Python (backend)

- Python ≥3.11. Dependency management: `uv` (fallback: `pip` + `requirements.txt`). Always a virtualenv.
- Lint + format: `ruff` (`ruff check` + `ruff format`). Config in `pyproject.toml`.
- Type hints on all public functions; `mypy` on Tier 2+ projects.
- Structure: `src/<package>/` layout, `tests/` mirroring `src/`. No logic in `__init__.py`.
- FastAPI conventions: routers per domain (`routers/`), Pydantic models in `schemas/`, business logic in `services/` — never in route handlers.
- Errors: raise specific exceptions; no bare `except:`. Log with `logging`, never `print`, in anything beyond a script.

## JS/TS (frontend)

- TypeScript, not JS, for anything beyond a throwaway page. `strict: true`.
- Framework default: Next.js (App Router). Vite + React for pure SPAs.
- Lint + format: ESLint + Prettier, config committed.
- Structure: `components/` (dumb, reusable), `app/` or `pages/` (routes), `lib/` (clients, utils), `hooks/`.
- State: server state via fetch/React Query; avoid global state libs until pain is real.
- API calls only through a typed client in `lib/api.ts` — never inline `fetch` in components.

## Testing

- Python: `pytest`. JS: `vitest`. Test files adjacent or in `tests/`, named `test_*.py` / `*.test.ts`.
- Tier 1: none required. Tier 2: unit tests on core logic. Tier 3: unit + integration on every API endpoint; aim ~70% on business logic, don't chase 100%.
- Every bug fixed gets a regression test.

## AI-assisted coding rules

- `CLAUDE.md` in repo root, kept current — it links PRD, design, code plan, and these standards.
- One code-plan task per session. Paste the task's acceptance criteria into the prompt.
- Review AI diffs before committing — you own every line. If you can't explain it, don't merge it.
- AI writes tests alongside features, in the same task.

## Definition of done (per task)

1. Acceptance criteria met
2. Lint + format pass
3. Tests (per tier) pass
4. Committed with a conventional message
5. Docs updated if behavior changed
