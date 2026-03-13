# fixtures/

This directory contains controlled fixture target repositories and population data
used by the bootstrap self-test harness (`scripts/run_fixture_selftest.py`).

Fixtures exist to provide **repeatable, evidence-friendly proof** that the bootstrap
apply and validate workflow works end-to-end.

---

## Purpose

The fixtures prove:

- `apply_bootstrap.py` correctly stages scaffold files into a target repo.
- Scaffolded files contain expected `{{PLACEHOLDER}}` markers (State B).
- A minimally populated target passes `validate_bootstrap.py` with no errors (State C).
- Future changes to templates, prompts, apply logic, or validation logic can be
  regression-tested against known fixture shapes.

Fixtures are **not** production code or real infrastructure.
They are intentionally minimal — small enough to inspect at a glance.

---

## Directory layout

```
fixtures/
├─ targets/
│  ├─ minimal-python-service/     ← code-oriented fixture (Flask, pytest)
│  │  ├─ README.md
│  │  ├─ pyproject.toml
│  │  ├─ src/app.py
│  │  └─ tests/test_smoke.py
│  └─ minimal-infra-repo/         ← infra/docs-oriented fixture (Terraform)
│     ├─ README.md
│     ├─ docs/architecture.md
│     └─ environments/dev/placeholder.tfvars.example
├─ population/
│  ├─ minimal-python-service.json ← State C proof data (placeholder values)
│  └─ minimal-infra-repo.json     ← State C proof data (placeholder values)
└─ README.md                      ← this file
```

---

## Fixture states

Three clearly defined states exist for each fixture during a self-test run:

### State A — raw fixture

The canonical fixture as committed in this repository. No bootstrap files are
present. This is the starting point for each test run.

**Characteristics:**
- Only the original fixture files (README, source code, config files)
- No `AGENTS.md`, `IMPLEMENTATION_TRACKER.md`, `docs/ai/`, `bootstrap/`, or
  `artifacts/ai/` directories

### State B — scaffold applied

`apply_bootstrap.py` has been run against a working copy of the fixture.
All required bootstrap files are present, but all `{{PLACEHOLDER}}` markers
remain unfilled. This is **expected behavior** — apply stages the scaffold
but does not populate repo-specific content.

**Characteristics:**
- All 7 bootstrap scaffold files are present
- `bootstrap/BOOTSTRAP_SOURCE.md` has bootstrap-system fields filled (source, version, date)
- All other markdown files contain `{{PLACEHOLDER}}` markers
- `validate_bootstrap.py --target-dir` will report placeholder failures — **this is correct**

### State C — minimally populated

Population data from `fixtures/population/<fixture-name>.json` has been applied
to a State B working copy, replacing all `{{PLACEHOLDER}}` markers with
fixture-specific proof values.

**Characteristics:**
- All bootstrap scaffold files are present and filled
- No `{{PLACEHOLDER}}` markers remain in any checked file
- `validate_bootstrap.py --target-dir` passes with zero failures

**Important:** State C population data is **fixture-only proof data**.
It is not real project discovery content and does not represent how a real
agent would populate a target repo. It exists only to prove that a fully
populated bootstrap passes validation.

---

## Fixture descriptions

### minimal-python-service

A minimal Flask HTTP service with two endpoints (`/` and `/health`).

- **Shape:** code-oriented (Python service)
- **Why:** proves bootstrap works for a typical application codebase shape
- **Stack:** Python, Flask, pytest, ruff
- **Files:** `src/app.py`, `tests/test_smoke.py`, `pyproject.toml`

### minimal-infra-repo

A minimal Terraform infrastructure repository with one environment (dev).

- **Shape:** infrastructure/documentation-oriented
- **Why:** proves bootstrap works for a non-application, docs-heavy repo shape
- **Stack:** Terraform (HCL), Markdown documentation
- **Files:** `docs/architecture.md`, `environments/dev/placeholder.tfvars.example`

---

## Population data format

Each `fixtures/population/<fixture-name>.json` file contains:

```json
{
  "_description": "Human-readable note about this proof data",
  "placeholder_values": {
    "PLACEHOLDER_NAME": "replacement value",
    ...
  },
  "file_overrides": {
    "relative/path/to/file": "full file content"
  }
}
```

- `placeholder_values`: applied globally to all `TARGET_PLACEHOLDER_FILES`
  by replacing `{{PLACEHOLDER_NAME}}` with the corresponding value
- `file_overrides`: replaces an entire file with the provided content
  (optional; used when a placeholder replacement approach is insufficient)

Population data covers all placeholders found in:
`AGENTS.md`, `IMPLEMENTATION_TRACKER.md`, `docs/ai/REPO_MAP.md`,
`docs/ai/SOURCE_REFRESH.md`, `docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md`,
`bootstrap/BOOTSTRAP_SOURCE.md`

---

## Running the self-tests

### Run all fixtures (State B + State C)

```bash
python scripts/run_fixture_selftest.py
```

### Run a specific fixture

```bash
python scripts/run_fixture_selftest.py --fixture minimal-python-service
python scripts/run_fixture_selftest.py --fixture minimal-infra-repo
```

### State B only (scaffold staging proof, skip population)

```bash
python scripts/run_fixture_selftest.py --state-b-only
```

### Inspect working copies after the run

```bash
python scripts/run_fixture_selftest.py --keep-work-dir --verbose
```

### Use a specific work directory

```bash
python scripts/run_fixture_selftest.py --work-dir /tmp/my-selftest
```

---

## Interpreting results

### Expected output (all passing)

```
Bootstrap self-test
  Bootstrap root : /path/to/agent-bootstrap
  Work directory : /tmp/bootstrap-selftest-XXXX
  Fixtures       : minimal-python-service, minimal-infra-repo
  Mode           : State B + State C

──────────────────────────────────────────────────────────────
  Fixture: minimal-python-service
──────────────────────────────────────────────────────────────

  State B — scaffold applied (placeholders expected)
  apply  : 7 file(s) created  [OK]
  validate (State B): 156 unfilled placeholder(s) — EXPECTED  [OK]

  State C — minimally populated (validation should pass)
  validate (State C): PASSED  [OK]

──────────────────────────────────────────────────────────────
  Fixture: minimal-infra-repo
──────────────────────────────────────────────────────────────
  ...

════════════════════════════════════════════════════════════
  Summary
════════════════════════════════════════════════════════════
  minimal-python-service                    B:PASS  C:PASS
  minimal-infra-repo                        B:PASS  C:PASS

SELF-TEST PASSED.
```

### What `B:PASS` means

State B passed: `apply_bootstrap.py` created all 7 scaffold files **and**
`validate_bootstrap.py` correctly found unfilled placeholders (proving the
scaffold was staged but not yet populated — expected behavior).

### What `C:PASS` means

State C passed: after applying population data, `validate_bootstrap.py`
found **no unfilled placeholders** and all checks passed.

### What failure looks like

- `B:FAIL` — `apply_bootstrap.py` errored, or the validator did not find
  expected placeholders (scaffold may be broken)
- `C:FAIL` — After population, the validator still failed (either a
  placeholder was missed in population data, or a required file is missing)
- `C:SKIP` — No population file found; State C was not tested

---

## When to update fixtures

Update fixtures when:

1. A new template adds a `{{PLACEHOLDER}}` that is not covered by existing
   population data — update the appropriate `fixtures/population/*.json` file.

2. The fixture's source files change meaningfully — update `fixtures/targets/`.

3. A new fixture type is needed to prove a new repo shape — add under
   `fixtures/targets/` and create corresponding population data.

**Do not:**
- Bloat fixtures with unnecessary files
- Use fixtures to test non-bootstrap concerns
- Let State C population data go stale after template changes

---

## Safety guarantees

The self-test harness **never mutates the canonical fixture source directories**.

All operations happen on temporary working copies created from the canonical
source. Working copies are removed after each run unless `--keep-work-dir` is
passed.

This means repeated self-test runs always start from the same clean State A.
