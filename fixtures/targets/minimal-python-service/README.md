# minimal-python-service

A minimal Python HTTP service. Used as a fixture target for bootstrap self-tests.

This is a **fixture repository** — intentionally minimal and not production code.

## Purpose

Demonstrates a code-oriented target repository shape for the agent-bootstrap self-test harness.

## Stack

- Python 3.11
- Flask (lightweight HTTP service)
- pytest (tests)
- ruff (linting)

## Structure

```
src/
  app.py         — Flask application entry point
tests/
  test_smoke.py  — Basic smoke tests
pyproject.toml   — Project metadata and dependencies
```

## Commands

```bash
pip install -e .[dev]
pytest
ruff check src/
python src/app.py
```
