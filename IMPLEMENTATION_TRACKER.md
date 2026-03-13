# IMPLEMENTATION_TRACKER.md

Live state file for the `agent-bootstrap` repository.  
Update this file at every milestone boundary. Do not let it go stale.

---

## Current phase

**Phase: Milestone 11 complete — Bootstrap Refresh / Upgrade Path**

---

## Objective

Build a reusable, production-grade AI agent bootstrap repository that serves as a canonical source of truth for initializing and operating AI-assisted target repositories.

---

## Milestone status

| # | Milestone | Status | Notes |
|---|-----------|--------|-------|
| 1 | Inspect and plan | ✅ Complete | Repo was near-empty: only LICENSE + README stub ("# agent-bootstrap") |
| 2 | Core control plane | ✅ Complete | README.md, AGENTS.md, IMPLEMENTATION_TRACKER.md, bootstrap-manifest.yaml |
| 3 | Prompt library | ✅ Complete | 5 prompt files created under prompts/ |
| 4 | Templates and schemas | ✅ Complete | 7 templates + 2 JSON schemas created |
| 5 | Validation and examples | ✅ Complete | validate_bootstrap.py + 4 example-notes.md files; script runs clean |
| 6 | Closeout | ✅ Complete | Tracker updated; README verified; validation recorded below |
| 7 | Dogfood and tighten | ✅ Complete | Validated bootstrap against itself; fixed `--target-dir` gap; strengthened prompts and templates |
| 8 | Target Repo Apply Path | ✅ Complete | `apply_bootstrap.py` created; manifest, README, AGENTS.md updated |
| 9 | End-to-End Fixtures and Self-Test Harness | ✅ Complete | 2 fixture repos, population data, self-test runner; both fixtures B:PASS C:PASS |
| 10 | GitHub Actions CI Regression Gate | ✅ Complete | `.github/workflows/ci.yml` created; runs validate + self-test on push/PR |
| 11 | Bootstrap Refresh / Upgrade Path | ✅ Complete | `refresh_bootstrap.py` created; manifest updated with refresh section; State D self-test; README/AGENTS updated |

---

## Decisions made

| Decision | Reason | Alternative considered |
|----------|--------|----------------------|
| No external Python dependencies in validate_bootstrap.py | Keep script dependency-light and portable | jsonschema library (rejected: adds install step) |
| Use `{{PLACEHOLDER}}` style for template markers | Visually obvious; grep-able | `<PLACEHOLDER>` (rejected: conflicts with HTML in some renderers) |
| templates/docs/ai/ and templates/artifacts/ai/ directory structure mirrors target-repo layout | Makes agent population deterministic | Flat templates/ dir (rejected: ambiguous target placement) |
| bootstrap-manifest.yaml uses YAML not JSON | More human-readable for a control plane file | JSON (acceptable but less readable for humans) |
| validate_bootstrap.py checks bootstrap repo files, not target repo files | Script is run against this repo to confirm scaffold integrity | Dual-mode script (deferred to future milestone) |
| .gitignore added for __pycache__ and .pyc files | Prevent Python build artifacts from being committed | Not adding (rejected: would pollute git status) |
| Added `--target-dir` flag to validate_bootstrap.py | Enables automated validation of bootstrapped target repos; was listed as open improvement; README already referenced this flag but it didn't exist | Separate script (rejected: unnecessary duplication) |
| Moved universal forbidden actions to the fixed list in AGENTS.md.template | Agents were filling `{{FORBIDDEN_ACTION_1/2}}` with generic content; concrete defaults + repo-specific override placeholders produce better output | All placeholders (rejected: too easy to leave blank) |
| Created `scripts/apply_bootstrap.py` using static template mappings | Manifest-driven mapping was considered but the static list is simpler, readable, and correct for the current template set; can be made fully manifest-driven later if needed | Full manifest-parsing (deferred: adds complexity for negligible benefit now) |
| apply_bootstrap.py fills only bootstrap-system placeholders in BOOTSTRAP_SOURCE.md | Repo-specific discovery content must remain agent-led; only metadata known at apply time (source URL, SHA, date) is filled automatically | Fill all placeholders automatically (rejected: would require guessing) |

---

## Files created in this run

### Root
- `README.md` — replaced stub with full content
- `AGENTS.md` — new; execution contract
- `IMPLEMENTATION_TRACKER.md` — this file; new
- `bootstrap-manifest.yaml` — new; machine-readable control plane
- `.gitignore` — new; minimal

### prompts/
- `prompts/new-repo-bootstrap.md`
- `prompts/existing-repo-discovery.md`
- `prompts/resume-work.md`
- `prompts/bounded-implementation.md`
- `prompts/closeout-and-handoff.md`

### templates/
- `templates/AGENTS.md.template`
- `templates/IMPLEMENTATION_TRACKER.md.template`
- `templates/bootstrap/BOOTSTRAP_SOURCE.md.template`
- `templates/docs/ai/REPO_MAP.md.template`
- `templates/docs/ai/SOURCE_REFRESH.md.template`
- `templates/docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template`
- `templates/artifacts/ai/repo_discovery.json.template`

### examples/
- `examples/python-service/example-notes.md`
- `examples/infra-repo/example-notes.md`
- `examples/vscode-extension/example-notes.md`
- `examples/kubernetes-platform/example-notes.md`

### schemas/
- `schemas/implementation_tracker.schema.json`
- `schemas/repo_discovery.schema.json`

### scripts/
- `scripts/validate_bootstrap.py`

---

## Decisions made in Milestone 9 (end-to-end fixtures and self-test harness)

| Decision | Reason | Alternative considered |
|----------|--------|----------------------|
| Two fixture shapes (Python service + infra/docs) | Proves bootstrap works on distinct repo shapes: code-oriented vs docs/infra-oriented | Single fixture (rejected: insufficient coverage) |
| Population JSON uses flat `placeholder_values` dict | Simple and explicit; maps placeholder names to values; applies globally to all checked files | Per-file replacement or full file overrides (deferred: overkill for this use case; `file_overrides` key exists for future use) |
| `{{PLACEHOLDER}}` meta-marker mapped to empty string in population data | The marker appears in template instruction comments; replacing with "" removes it cleanly | Leaving it unfilled (rejected: would cause State C validation to fail) |
| Self-test runner copies fixtures to temp working dirs | Canonical fixture sources must never be mutated during tests; temp dirs are auto-cleaned | In-place mutation (rejected: would corrupt canonical fixtures) |
| State B expected to FAIL validation | Proves apply staged the scaffold correctly but left placeholders for agent population | Requiring State B to pass (rejected: would require pre-filling placeholders, defeating purpose) |
| No heavy test framework; pure Python stdlib | Keeps the harness dependency-free and readable; consistent with validate_bootstrap.py and apply_bootstrap.py | pytest (deferred: adds install step; stdlib subprocess is sufficient) |
| `run_fixture_selftest.py` required in BOOTSTRAP_REPO_REQUIRED_FILES | Prevents drift where the harness exists but isn't tracked as required | Not required (rejected: would allow silent deletion) |

---

## Files created/modified in Milestone 9 (end-to-end fixtures and self-test harness)

### fixtures/ (new directory)
- `fixtures/README.md` — fixture documentation: purpose, states, usage, update guidance
- `fixtures/targets/minimal-python-service/README.md` — fixture overview
- `fixtures/targets/minimal-python-service/pyproject.toml` — project metadata
- `fixtures/targets/minimal-python-service/src/app.py` — minimal Flask HTTP service
- `fixtures/targets/minimal-python-service/tests/test_smoke.py` — smoke tests
- `fixtures/targets/minimal-infra-repo/README.md` — fixture overview
- `fixtures/targets/minimal-infra-repo/docs/architecture.md` — architecture doc
- `fixtures/targets/minimal-infra-repo/environments/dev/placeholder.tfvars.example` — example Terraform vars
- `fixtures/population/minimal-python-service.json` — State C proof data (116 placeholder values)
- `fixtures/population/minimal-infra-repo.json` — State C proof data (116 placeholder values)

### scripts/
- `scripts/run_fixture_selftest.py` — new; end-to-end self-test harness

### Root
- `AGENTS.md` — added third operational surface; added fixture and self-test rules section
- `IMPLEMENTATION_TRACKER.md` — this file; Milestone 9 recorded
- `bootstrap-manifest.yaml` — added new required files; added `fixtures:` section
- `README.md` — added fixtures/self-test section; updated repository layout
- `scripts/validate_bootstrap.py` — added 6 new files to `BOOTSTRAP_REPO_REQUIRED_FILES`

---



### scripts/
- `scripts/apply_bootstrap.py` — new; manifest-driven scaffold apply script

### Root
- `AGENTS.md` — added operational surfaces section and apply script context
- `IMPLEMENTATION_TRACKER.md` — this file; Milestone 8 recorded
- `bootstrap-manifest.yaml` — added `apply:` section with template mappings and auto-filled placeholder list
- `README.md` — added "Applying bootstrap to a target repo" section with commands, examples, and apply vs discovery distinction
- `scripts/validate_bootstrap.py` — added `scripts/apply_bootstrap.py` to required files list

---

## Files modified in Milestone 7 (dogfood and tighten)

- `scripts/validate_bootstrap.py` — added `--target-dir` mode, placeholder detection (`check_placeholders`), and refactored `check_required_files` to accept a file list
- `prompts/new-repo-bootstrap.md` — Step 10: added concrete grep command and `--target-dir` reference
- `prompts/closeout-and-handoff.md` — Step 2: added concrete grep and JSON validation commands
- `templates/AGENTS.md.template` — moved universal forbidden actions to fixed list; repo-specific placeholders now clearly labeled with richer examples
- `templates/IMPLEMENTATION_TRACKER.md.template` — expanded decisions table to two example rows with richer comments; updated validation status table to show concrete commands

---

## Validation status

| Check | Result | Method |
|-------|--------|--------|
| All required bootstrap repo files present | ✅ Pass | `python scripts/validate_bootstrap.py` |
| README.md layout matches actual file tree | ✅ Pass | Manual cross-check |
| bootstrap-manifest.yaml parseable | ✅ Pass | `python -c "import yaml; yaml.safe_load(open('bootstrap-manifest.yaml'))"` |
| JSON schemas are valid JSON | ✅ Pass | `python -m json.tool schemas/*.json` |
| repo_discovery.json.template is valid JSON | ✅ Pass | `python -m json.tool` |
| validate_bootstrap.py exits 0 | ✅ Pass | Direct execution |
| Python script syntax | ✅ Pass | `python -m py_compile scripts/validate_bootstrap.py` |
| `--target-dir` mode detects missing files | ✅ Pass | `python scripts/validate_bootstrap.py --target-dir /tmp` (7 failures expected) |
| `--target-dir` mode detects unfilled placeholders | ✅ Pass | Manual test with synthetic target dir |
| `--target-dir` mode validates JSON artifacts | ✅ Pass | Manual test with valid repo_discovery.json |
| apply_bootstrap.py syntax check | ✅ Pass | `python -m py_compile scripts/apply_bootstrap.py` |
| apply_bootstrap.py dry-run (empty target) | ✅ Pass | 7 files reported [CREATED], no files written |
| apply_bootstrap.py actual apply | ✅ Pass | 7 files created, marker rendered with source/version/date |
| apply_bootstrap.py skip behavior | ✅ Pass | Re-run shows all 7 [SKIPPED]; exits 0 |
| apply_bootstrap.py --force --dry-run | ✅ Pass | All 7 shown as [WOULD OVERWRITE]; exits 0 |
| validate_bootstrap.py on applied target | ✅ Pass | Required files present; placeholder failures expected (agent fills them) |
| validate_bootstrap.py on bootstrap source repo | ✅ Pass | All required files including apply_bootstrap.py detected |
| run_fixture_selftest.py syntax check | ✅ Pass | `python -m py_compile scripts/run_fixture_selftest.py` |
| Self-test: minimal-python-service State B | ✅ Pass | 7 files created; 140 unfilled placeholders detected (expected) |
| Self-test: minimal-python-service State C | ✅ Pass | All 14 checks passed; 0 unfilled placeholders |
| Self-test: minimal-infra-repo State B | ✅ Pass | 7 files created; 140 unfilled placeholders detected (expected) |
| Self-test: minimal-infra-repo State C | ✅ Pass | All 14 checks passed; 0 unfilled placeholders |
| Full self-test run | ✅ Pass | `python scripts/run_fixture_selftest.py` exits 0; B:PASS C:PASS for both fixtures |
| ci.yml YAML validity | ✅ Pass | Inspected for valid YAML structure and two-space indentation |
| ci.yml workflow triggers | ✅ Pass | push, pull_request, workflow_dispatch all present |
| ci.yml regression commands | ✅ Pass | py_compile, validate_bootstrap.py, run_fixture_selftest.py all present |
| Local equivalents of CI commands | ✅ Pass | All three commands run locally and exit 0 |
| refresh_bootstrap.py syntax check | ✅ Pass | `python -m py_compile scripts/refresh_bootstrap.py` |
| refresh_bootstrap.py dry-run on empty target | ✅ Pass | 7 files [WOULD CREATE]; bootstrap marker not detected; exits 0 |
| refresh_bootstrap.py dry-run on freshly applied target | ✅ Pass | 6 [UNCHANGED], 1 [WOULD REFRESH] (marker has {{BOOTSTRAP_NOTES}}); exits 0 |
| refresh_bootstrap.py on populated target | ✅ Pass | All populated files [SKIPPED]; exits 0 |
| validate_bootstrap.py detects refresh_bootstrap.py | ✅ Pass | Script added to BOOTSTRAP_REPO_REQUIRED_FILES; validate exits 0 |
| Self-test State D: minimal-python-service | ✅ Pass | 6 populated files skipped, 0 would change |
| Self-test State D: minimal-infra-repo | ✅ Pass | 6 populated files skipped, 0 would change |
| Full self-test with State D | ✅ Pass | `python scripts/run_fixture_selftest.py` exits 0; B:PASS C:PASS D:PASS for both fixtures |

---

## Decisions made in Milestone 10 (GitHub Actions CI regression gate)

| Decision | Reason | Alternative considered |
|----------|--------|----------------------|
| Single `regression` job, no matrix | The scripts have no external dependencies and run fast; a matrix adds complexity for no benefit at this stage | Multi-job or matrix (deferred: no current evidence of need) |
| Python 3.11 only | Stable LTS version; scripts use only stdlib; no third-party dependency version matrix needed | 3.x latest or multi-version matrix (rejected: overkill given stdlib-only scripts) |
| `actions/checkout@v4` and `actions/setup-python@v5` | Current stable major versions for these standard actions | Older versions (rejected: best to use maintained versions) |
| Separate "syntax check" step before main commands | Catches import/syntax errors with a clear label before running logic; cheap and explicit | Relying on script exit codes alone (rejected: harder to debug which step failed) |
| No dependency caching | No `pip install` step; nothing to cache | Caching (rejected: unnecessary overhead with no dependencies) |
| No branch filtering | No established branch convention in this repo; keeping triggers general is safer | `branches: [main]` filter (rejected: would miss branch-level regression detection) |

---

## Files created/modified in Milestone 10 (GitHub Actions CI regression gate)

### .github/ (new directory)
- `.github/workflows/ci.yml` — new; GitHub Actions workflow: syntax check, validate_bootstrap.py, run_fixture_selftest.py

### Root
- `AGENTS.md` — added CI regression gate section with rules for agents
- `IMPLEMENTATION_TRACKER.md` — this file; Milestone 10 recorded
- `README.md` — added "Continuous integration" section with what it checks, when it runs, and what regressions it catches

---

## Decisions made in Milestone 11 (bootstrap refresh / upgrade path)

| Decision | Reason | Alternative considered |
|----------|--------|----------------------|
| New script `scripts/refresh_bootstrap.py` rather than extending `apply_bootstrap.py` | Refresh has distinct semantics (classification, skip-populated logic, lifecycle detection) that would clutter the apply path; a separate script is clearer and independently testable | Extending apply_bootstrap.py (rejected: would create confusing overlap of behaviors) |
| File classification based on presence of unfilled `{{PLACEHOLDER}}` markers | Most reliable practical signal for "not yet populated by an agent"; does not require storing prior template snapshots | Hash-based comparison to prior bootstrap version (rejected: requires storing template snapshots; no prior snapshots exist) |
| Four classifications: missing / unchanged / safe-refresh / populated | Covers all observable states; maps cleanly to safe actions; avoids invented complexity | More granular states (rejected: unnecessary without evidence of need) |
| `safe-if-unpopulated` vs `manual-review` refresh policies per file | IMPLEMENTATION_TRACKER.md and repo_discovery.json are always populated early; other scaffold files may remain unpopulated; explicit per-file policy avoids guessing | Single policy for all files (rejected: would either be too aggressive or too conservative) |
| State D in self-test harness: refresh --dry-run on State C fixture | Provides bounded, repeatable proof of non-destructive behavior; cheap to run | Separate integration test suite (rejected: overkill; State D fits cleanly into existing harness) |
| Manifest `refresh:` section added | Documents the policy machine-readably; makes file classification decisions visible and auditable | Inline-only in the script (rejected: harder to inspect without reading code) |
| Bootstrap marker (`bootstrap/BOOTSTRAP_SOURCE.md`) classified as `marker` policy | Marker file has auto-filled bootstrap-system values; standard placeholder detection would misclassify it | Same as other files (rejected: marker has different semantics from scaffold files) |

---

## Files created/modified in Milestone 11 (bootstrap refresh / upgrade path)

### scripts/
- `scripts/refresh_bootstrap.py` — new; safe refresh/upgrade script with classification logic

### Root
- `AGENTS.md` — updated operational surfaces (3→4); added lifecycle section; added forbidden action for overwriting populated files
- `IMPLEMENTATION_TRACKER.md` — this file; Milestone 11 recorded
- `bootstrap-manifest.yaml` — added `scripts/refresh_bootstrap.py` to required files; added `refresh:` section with classification policies
- `README.md` — added "Refreshing an already-bootstrapped target repo" section; added apply vs refresh vs validate table; updated CI regressions note
- `.github/workflows/ci.yml` — added `scripts/refresh_bootstrap.py` to syntax check step

### scripts/ (modified)
- `scripts/validate_bootstrap.py` — added `scripts/refresh_bootstrap.py` to `BOOTSTRAP_REPO_REQUIRED_FILES`
- `scripts/run_fixture_selftest.py` — added `run_refresh()` helper; added State D test (refresh --dry-run on populated fixture); updated summary line to show D label

---

## Open improvements (future milestones)

- [x] Add `--target-dir` mode to `validate_bootstrap.py` to validate a bootstrapped target repo ✅ Done (Milestone 7)
- [x] Add `scripts/apply_bootstrap.py` to stage scaffold into target repos safely ✅ Done (Milestone 8)
- [x] Add end-to-end fixture self-test harness ✅ Done (Milestone 9)
- [ ] Add a `jsonschema`-based validation mode (optional, behind `--strict` flag)
- [x] Add a GitHub Actions workflow to run `validate_bootstrap.py` and `run_fixture_selftest.py` on push ✅ Done (Milestone 10)
- [x] Add a safe refresh/upgrade path for already-bootstrapped target repos ✅ Done (Milestone 11)
- [ ] Expand examples with concrete file trees and discovery findings
- [ ] Add a `prompts/target-repo-audit.md` for ongoing maintenance sessions
- [ ] Consider adding a `CHANGELOG.md` when this repo has meaningful version history
- [ ] Add CODEOWNERS or similar if this becomes a shared team resource
- [ ] Make `apply_bootstrap.py` and `refresh_bootstrap.py` fully read template mappings
  from `bootstrap-manifest.yaml` rather than the static fallback list (currently in sync;
  unifying reduces future drift)

---

## Next strongest bounded milestone

**Milestone 12 — jsonschema-based strict validation (optional)**

Scope:
- Add a `--strict` flag to `validate_bootstrap.py` that uses `jsonschema` (if installed)
  to validate `artifacts/ai/repo_discovery.json` against `schemas/repo_discovery.schema.json`
- Falls back gracefully if `jsonschema` is not installed
- Keeps the default validation path dependency-free

Estimated size: Small (1 file modified: `scripts/validate_bootstrap.py`)
