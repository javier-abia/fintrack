# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Fintrack is a financial tracker application with a FastAPI backend (`apps/api/`) and a frontend placeholder (`apps/web/`). Infrastructure lives in `infra/`.

## Design documents

Primary docs live in the repo at `docs/`. Consult before writing or reviewing non-trivial code:

- `docs/architecture.md` — system diagram, component responsibilities, CSV ingestion flow, Etherscan/CoinGecko integration points.
- `docs/data-model.md` — all DB tables with field types, constraints, currency handling, crypto wallet validation, and soft-delete semantics.
- `docs/features.md` — MVP features with acceptance criteria; use as the definition of done when implementing or reviewing feature work.

The remaining files (`docs/tech-stack.md`, `docs/deployment.md`, `docs/dev-tooling.md`) cover tech-stack rationale, deployment, and tooling — useful for project-level decisions but not needed during routine coding sessions.

An older copy of the docs may also exist at `/home/jabia/Documents/Obsidian/Projects/Financial-tracker/docs/` — prefer the in-repo `docs/` when both are present.

## Commands

All Python tooling uses `uv`. Run commands from the repo root unless noted.

```bash
# Install dependencies
uv sync

# Run the API dev server
uv run uvicorn fintrack_api.main:app --reload

# Lint
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy apps/api/src/

# Run tests
uv run pytest

# Run a single test file
uv run pytest apps/api/tests/path/to/test_file.py

# Database migrations
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
```

## Architecture

**Monorepo** managed as a `uv` workspace (root `pyproject.toml` lists `apps/api` as a member). Python ≥ 3.14 required.

**Backend (`apps/api/`)** — FastAPI + SQLAlchemy (async) + aiosqlite + Alembic. Pydantic (with email) handles validation; pydantic-settings manages config. Uvicorn serves the ASGI app.

**Frontend (`apps/web/`)** — not yet scaffolded.

**Infrastructure (`infra/`)** — docker-compose and Caddyfile are placeholder files, not yet configured.

## Code style

- Ruff enforces rules E, F, I, UP, B, SIM at line length 88 (E501 ignored).
- MyPy runs in strict mode targeting Python 3.14.
- Tests use pytest with `asyncio_mode = "auto"` — all async tests work without explicit decorators.

## GitHub CLI extensions

- `valeriobelli/gh-milestone` — manage milestones via `gh milestone`

## GitHub issues and milestones

Do **not** use "Phase" or "Step" nomenclature in milestone or issue titles/descriptions, even if the docs use that language. Name by feature area or deliverable instead (e.g. "Authentication", "CSV Ingestion", "Wallet tracking").

## Gitflow

One issue per task. One short-lived branch per issue, branched from `main`:

```bash
git checkout -b issue/42-short-description
```

Open a PR that references the issue (`Closes #42`) — merging to `main` closes it automatically. `main` is always in a working state.

## Commits

Use Conventional Commits. Format: `type(scope): description`

- Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`, `ci`
- Scope: area of the codebase, e.g. `backend`, `frontend`, `infra`, `db`, `auth`
- Example: `feat(backend): initialize skeleton for API endpoints`
- Do **not** add `Co-Authored-By` trailers.
