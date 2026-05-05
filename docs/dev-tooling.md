# 8. Dev tooling

A learning-focused walkthrough of the day-to-day dev loop: dependency
management, linting, typing, pre-commit, and CI. The high-level choices live in
[`03-tech-stack.md`](03-tech-stack.md); this doc is the "how to actually use
them" companion.

## The dev loop, in one picture

```
edit code
   │
   ▼
ruff format / ruff check --fix      ← cheap, automatic
   │
   ▼
mypy --strict   |   tsc --noEmit    ← types must pass
   │
   ▼
pytest          |   vitest          ← tests must pass
   │
   ▼
git commit  ──► pre-commit re-runs the cheap steps
   │
   ▼
git push    ──► GitHub Actions re-runs everything in a clean env
```

Pre-commit catches what you forgot locally. CI catches what your machine
silently had installed.

## Backend: `uv` (Astral)

`uv` replaces `pip`, `pip-tools`, `virtualenv`, and `pyenv` with one tool
written in Rust. It's ~10–100× faster than pip and writes a real lockfile.

### One-time install

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Bootstrap the API project

```bash
cd apps/api
uv init --package          # creates pyproject.toml + src/ layout
uv python pin 3.12         # writes .python-version
uv add fastapi 'uvicorn[standard]' sqlalchemy alembic pydantic-settings \
       'passlib[bcrypt]' apscheduler httpx loguru
uv add --dev pytest pytest-asyncio ruff mypy types-passlib
```

`uv add` updates `pyproject.toml` *and* `uv.lock` in one step. Commit both.

### Daily commands

| Command | What it does |
|---|---|
| `uv sync` | Install exactly what's in the lockfile into `.venv/` |
| `uv add <pkg>` | Add a runtime dependency, update lock |
| `uv add --dev <pkg>` | Add a dev-only dependency |
| `uv remove <pkg>` | Drop a dependency |
| `uv lock --upgrade` | Refresh the lock to latest allowed versions |
| `uv run <cmd>` | Run a command inside the project venv (no `activate` needed) |
| `uv run pytest` | The way you'll run tests 90% of the time |

You almost never `pip install` anything. If a tutorial says "pip install X",
mentally translate to `uv add X`.

### Why this matters for learning

A real lockfile (`uv.lock`) means "works on my machine" stops being a thing —
the Pi, CI, and your laptop install the *same* resolved versions. This is the
same property `package-lock.json` and `Cargo.lock` give you.

## Backend: `ruff` (lint + format)

`ruff` is a single tool that replaces `black`, `isort`, `flake8`, `pylint`,
`pyupgrade`, and a dozen smaller plugins. Also Rust, also fast.

### Config (`pyproject.toml`)

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = [
  "E", "F",       # pyflakes + pycodestyle (the basics)
  "I",            # isort (import ordering)
  "B",            # bugbear (likely bugs)
  "UP",           # pyupgrade (modernize syntax)
  "SIM",          # simplifications
  "RUF",          # ruff-specific
]
ignore = ["E501"]  # line length is enforced by the formatter, not the linter

[tool.ruff.format]
quote-style = "double"
```

### Commands

```bash
uv run ruff format .          # rewrite files (replaces black)
uv run ruff check . --fix     # lint + auto-fix what's safe
uv run ruff check .           # lint only, exit non-zero on issues (CI mode)
```

## Backend: `mypy --strict`

Static type checking. `--strict` is opinionated — turn it on from day one or
it's painful to enable later.

### Config (`pyproject.toml`)

```toml
[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]
exclude = ["alembic/versions/"]

[[tool.mypy.overrides]]
module = ["apscheduler.*"]
ignore_missing_imports = true
```

### Run

```bash
uv run mypy src/
```

Expect to add a `types-*` stub package occasionally (`uv add --dev types-passlib`).

## Frontend: eslint + prettier + tsc

Mirrors of ruff/mypy on the JS side.

```bash
cd apps/web
pnpm create vite . --template react-ts
pnpm add -D eslint prettier eslint-config-prettier @types/node \
            eslint-plugin-react-hooks
```

Daily commands:

```bash
pnpm tsc --noEmit            # type-check (no JS output)
pnpm prettier --write .      # format
pnpm eslint . --fix          # lint
pnpm vitest                  # tests
```

(Use `pnpm` over `npm` — faster, smaller `node_modules`, real lockfile.)

## `pre-commit` — the glue

`pre-commit` is a Python tool that runs hooks on staged files before the
commit lands. It pulls each hook from its own repo at a pinned version, so
your contributors all run the same versions.

### Install

```bash
uv tool install pre-commit       # installs globally, isolated
pre-commit install               # adds .git/hooks/pre-commit to this repo
```

### `.pre-commit-config.yaml` (repo root)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.2
    hooks:
      - id: mypy
        files: ^apps/api/src/
        additional_dependencies:
          - pydantic
          - sqlalchemy[mypy]
          - types-passlib

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        files: ^apps/web/

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-yaml
      - id: check-added-large-files
```

### Daily use

You don't run it manually — `git commit` triggers it. Useful manual commands:

```bash
pre-commit run --all-files           # run every hook on the whole repo
pre-commit autoupdate                # bump every hook's `rev:` to latest
```

If a hook auto-fixes files, the commit aborts so you can re-stage and try
again. That's the intended flow.

### Why this matters

CI failures cost ~5 minutes each (push, wait, read logs, push again).
Pre-commit catches the same issues in <10 seconds at commit time. The
hooks pinned in `.pre-commit-config.yaml` and the versions pinned in
CI must agree, or you'll get drift bugs — keep them in sync deliberately.

## CI: GitHub Actions

One workflow file per concern. Start with this and only add more when needed.

### `.github/workflows/ci.yml`

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  api:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apps/api
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true

      - run: uv python install 3.12
      - run: uv sync --frozen          # fail if uv.lock is out of date

      - run: uv run ruff format --check .
      - run: uv run ruff check .
      - run: uv run mypy src/
      - run: uv run pytest -q

  web:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apps/web
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: 9 }
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
          cache-dependency-path: apps/web/pnpm-lock.yaml

      - run: pnpm install --frozen-lockfile
      - run: pnpm prettier --check .
      - run: pnpm eslint .
      - run: pnpm tsc --noEmit
      - run: pnpm vitest run
```

### Things to notice

- **`uv sync --frozen`** and **`pnpm install --frozen-lockfile`** are the
  CI-mode flags — they refuse to update the lockfile. If your code drifts
  from the lock, CI fails loudly instead of silently resolving new versions.
- **Two jobs, not one.** They run in parallel, each only sets up the toolchain
  it needs. Add a third `docker-build` job later for the `arm64` image.
- **No deploy step.** Phase-1 deploys are manual `git pull && docker compose up`
  on the Pi. Add a deploy job once you're tired of doing that by hand.

### Later: build & push the Pi image

When you're ready, add a `build-image` job using `docker/setup-qemu-action` +
`docker/build-push-action` with `platforms: linux/arm64`, pushing to GHCR.
Documented in [`06-deployment.md`](06-deployment.md#cicd-later).

## Quickstart cheat sheet

Once the implementation repo exists, day-to-day looks like:

```bash
# clone fresh
git clone <repo> && cd financial-app
pre-commit install
(cd apps/api && uv sync)
(cd apps/web && pnpm install)

# while coding (API)
cd apps/api
uv run uvicorn finapp.main:app --reload
uv run pytest -q
uv run ruff check . --fix && uv run ruff format .
uv run mypy src/

# while coding (web)
cd apps/web
pnpm dev
pnpm vitest
pnpm tsc --noEmit
```

## Recommended learning path

If this is your first time wiring all of this up, do it in this order — each
step gives you something working before adding the next:

1. **`uv` only.** Get the API running with `uv run uvicorn`. Commit `uv.lock`.
2. **Add `ruff`.** Configure, run once on the codebase, commit the reformat.
3. **Add `mypy --strict`.** Fix the failures (this is where you actually learn
   typing). Don't skip to the next step until it's clean.
4. **Add `pre-commit`.** Now your local environment enforces 1–3.
5. **Add GitHub Actions CI.** Do this at the end of Phase 1 (backend skeleton
   done, tests passing). A clean Linux box re-runs everything. The first green
   CI run is the real "the project is set up" moment. Full workflow in
   [`09-developer-roadmap.md`](09-developer-roadmap.md) Step 1.8.
6. **Mirror the same shape on the frontend** (`pnpm` + `eslint` + `prettier`
   + `tsc` + `vitest`). Add the `web` CI job at the end of Phase 2.

Don't try to set up all six at once on day one — you'll spend more time
debugging tooling than writing app code.
