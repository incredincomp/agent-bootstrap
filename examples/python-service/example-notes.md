# Example Notes: Python Service Repository

This document guides an agent performing discovery or bootstrap on a Python-based service repository.

---

## Likely repository characteristics

- Primary language: Python (3.8+)
- Build/packaging: `pyproject.toml` or `setup.py`; sometimes `Makefile` for task automation
- Package manager: `pip`, `poetry`, or `uv`
- Dependency files: `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, or `poetry.lock`
- Runtime version: `.python-version`, `pyproject.toml [tool.poetry.dependencies]`, or `.tool-versions`
- Test framework: `pytest` (most common), `unittest` (older projects)
- Lint/format: `flake8`, `ruff`, `black`, `mypy`, or a combination
- Common structure:
  - `src/<package_name>/` — application code
  - `tests/` — test files
  - `scripts/` — utility scripts
  - `docs/` — documentation (Sphinx, MkDocs, or plain markdown)

---

## What an agent should prioritize in discovery

1. **Entry point:** Find the main application entry point (e.g., `main.py`, `app.py`, `__main__.py`, CLI via `pyproject.toml [scripts]`).
2. **Dependency file:** Read `pyproject.toml` or `requirements.txt` for the actual dependency list — this reveals most of the tech stack.
3. **Test command:** Check `Makefile`, `pyproject.toml [tool.pytest.ini_options]`, or CI config for how tests are run.
4. **CI config:** `.github/workflows/` is the fastest way to understand the full build/test/deploy pipeline.
5. **Configuration management:** Look for `settings.py`, `config.py`, `.env.example`, or use of `pydantic-settings`, `dynaconf`, or `python-decouple`.
6. **Database:** Check for `sqlalchemy`, `alembic` (migrations), `tortoise-orm`, or `django` imports.
7. **API framework:** `fastapi`, `flask`, `django`, `aiohttp`, or `starlette` — determines routing and middleware patterns.

---

## Typical authoritative files

| File | Why authoritative |
|------|------------------|
| `pyproject.toml` or `setup.py` | Declares dependencies, entry points, build config |
| `requirements.txt` / `requirements-dev.txt` | Pinned dependencies (if not using pyproject) |
| `alembic.ini` or `migrations/` | Database migration state |
| `.env.example` | Environment variable contract |
| `Makefile` | Task automation (install, test, lint, run) |
| `Dockerfile` | Deployment unit definition |

---

## Common traps

- **Virtual environment included in repo:** If `venv/`, `.venv/`, or `env/` is not in `.gitignore`, do not inspect it — it is not application code.
- **Generated files:** `*_pb2.py` (protobuf), `*_generated.py`, or anything in `src/<pkg>/generated/` should not be edited directly.
- **Relative imports:** Python packages with complex relative import structures can be hard to navigate; trace from the entry point.
- **Multiple requirements files:** Some projects have `requirements.txt`, `requirements-dev.txt`, `requirements-test.txt` — check all to understand full dependency scope.
- **Django vs. non-Django:** Django projects have a very different structure (`manage.py`, `settings.py`, app-per-feature) — recognize the pattern early.
- **async code:** If the project uses `asyncio`, `httpx`, or `anyio`, tests may require special runner configuration (`pytest-asyncio`).

---

## Good first milestone after bootstrap

**Milestone 2 — Implement failing test coverage for the primary service layer**

Scope:
- Identify the primary business logic module (e.g., `src/<pkg>/services/`)
- Write `pytest` unit tests for the main service functions
- Confirm tests pass with `pytest tests/`
- Update `IMPLEMENTATION_TRACKER.md`

Why this milestone: It confirms the build environment works, establishes test patterns, and adds immediate value without risky refactoring.
