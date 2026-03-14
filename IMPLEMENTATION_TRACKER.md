# IMPLEMENTATION_TRACKER.md

Live state file for the `agent-bootstrap` repository.  
Update this file at every milestone boundary. Do not let it go stale.

---

## Current phase

**Phase: Milestone 18 complete — Target Repo Bootstrap Doctor / Audit Contract Test Expansion**

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
| 12 | Manifest-Driven Bootstrap Profiles | ✅ Complete | 5 profiles; `--profile` flag; profile written to marker; fixture proof B:PASS C:PASS D:PASS |
| 13–15 | Versioning, Status, Profiles | ✅ Complete | VERSION, CHANGELOG, bootstrap_status.py, suggest_profile.py; State E; 39 required files, 44 total checks |
| 16 | Target Repo Bootstrap Doctor / Audit Mode | ✅ Complete | `bootstrap_doctor.py`; 6 health states; State F fixture proof; README/AGENTS/tracker updated |
| 17 | Shared Bootstrap Core and Contract Tests | ✅ Complete | `bootstrap_core.py`; 6 scripts refactored; 39 contract tests; CI updated; 41 required files, 46 total checks |
| 18 | Doctor / Audit Contract Test Expansion | ✅ Complete | `tests/test_bootstrap_doctor.py`; 77 diagnosis contract tests; 42 required files, 47 total checks |
| 19 | Target Repo Audit JSON Schema Stabilization | ✅ Complete | `schemas/bootstrap_doctor_report.schema.json`; `--json` stabilized with `schema_version` and structured recommendations; 33 JSON contract tests; 43 required files, 49 total checks |
| CI | CI dedup + concurrency hardening | ✅ Complete | Narrowed `push` trigger to `main`; added workflow-level concurrency; AGENTS.md updated |

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

## Decisions made in Milestone 12 (manifest-driven bootstrap profiles)

| Decision | Reason | Alternative considered |
|----------|--------|----------------------|
| Five initial profiles: generic, python-service, infra-repo, vscode-extension, kubernetes-platform | Covers the most common distinct repo families; bounded initial set as specified; each profile has clear applicability | Fewer profiles (rejected: problem statement required all five); more profiles (deferred: YAGNI) |
| Only `AI_AGENT_VENDOR_KNOWLEDGE_BASE.md` has profile-specific variants | This is the template where repo-family-specific guidance (runtime, SDK, platform) is most relevant; all other templates are universal structural scaffolding | Per-profile variants for all templates (rejected: excessive complexity for marginal benefit) |
| PROFILES dict in apply/refresh scripts (not runtime manifest parsing) | Maintains the static-fallback pattern already established; readable and predictable; no YAML parsing required at runtime | Runtime YAML parsing (deferred: consistent with existing apply_bootstrap.py design) |
| apply fails clearly on unknown profiles; refresh falls back to generic with warning | Apply is the authoritative profile selection moment; unknown at apply time = mistake; unknown at refresh time (e.g., from old marker) = graceful degradation more appropriate | Both fail hard (rejected: would break refresh on repos bootstrapped without profiles) |
| BOOTSTRAP_PROFILE auto-filled in marker at apply time | Profile is a bootstrap-system value (like date and version), not a repo-specific discovery value; consistent with existing auto-fill pattern | Leave for agent to fill (rejected: profile is known at apply time; no reason to leave it blank) |
| Refresh reads profile from marker; no `--profile` flag on refresh | Profile is set at apply time and stored in the marker; refresh inherits it; adding a separate flag would create inconsistency risk | --profile flag on refresh (deferred: not needed; marker provides the authoritative value) |
| Fixture proof: minimal-python-service → python-service; minimal-infra-repo → infra-repo | These fixtures already represent the right repo shapes; mapping to their natural profiles provides proof without new fixtures | New dedicated profile fixtures (rejected: existing fixtures already cover the shapes) |

---

## Decisions made in Milestone 17 (shared bootstrap core and contract tests)

| Decision | Reason | Alternative considered |
|----------|--------|----------------------|
| New `scripts/bootstrap_core.py` module (not `scripts/_bootstrap_core.py`) | Public name is clearer; no need to signal "private" in a repo with no packaging | Underscore prefix (deferred: unnecessary signal for this non-package codebase) |
| Extracted: PLACEHOLDER_RE, SEMVER_RE, parse_marker, is_placeholder, PROFILES, read_version, classify_era, resolve_template_mappings | These were the most clearly duplicated semantics across 5+ scripts | Extracting everything (rejected: some logic is script-specific; over-extraction adds coupling) |
| `suggest_profile.py` keeps its own `PROFILES` dict (signal-based) | Its `PROFILES` dict maps to heuristic signal lists, not template overrides — different role; only profile *names* must match core | Importing from bootstrap_core (rejected: different data shape; would require awkward indirection) |
| Contract tests use stdlib `unittest` in a new `tests/` directory | Consistent with existing dependency-free approach; no pytest needed; small and readable | pytest (rejected: adds external dependency for no benefit at this test volume) |
| CI gains a new step between validate and selftest | Validates the contract tests run on CI; keeps order logical (structure → semantics → end-to-end) | Running tests inside selftest (rejected: different scopes; separate is cleaner) |
| Version bumped from 0.13.0 to 0.14.0 (minor bump) | New public module with a stable API surface; additive change to required files list | Patch bump (rejected: new module is a meaningful additive change) |
| Refresh `resolve_mappings()` merges refresh_policy from local TEMPLATE_MAPPINGS | `refresh_policy` is refresh-specific metadata not in the shared core; merging preserves local metadata without duplicating it in core | Adding refresh_policy to core (rejected: it's a refresh-specific concept) |

---

## Files created/updated in Milestone 17 (shared bootstrap core and contract tests)

### scripts/ (new file)
- `scripts/bootstrap_core.py` — new; shared semantic helpers for all bootstrap scripts

### tests/ (new directory)
- `tests/test_bootstrap_core.py` — new; 39 contract tests for bootstrap_core.py

### scripts/ (updated)
- `scripts/apply_bootstrap.py` — imports PROFILES, DEFAULT_PROFILE, read_version, resolve_template_mappings from bootstrap_core; removed local duplicates
- `scripts/refresh_bootstrap.py` — imports PLACEHOLDER_RE, PROFILES, DEFAULT_PROFILE, read_version, resolve_template_mappings, get_bootstrap_marker_path, parse_bootstrap_marker, has_placeholders from bootstrap_core; removed local duplicates
- `scripts/bootstrap_status.py` — imports SEMVER_RE, read_version, parse_bootstrap_marker, is_placeholder, classify_marker_era from bootstrap_core; removed local parse_marker/is_placeholder; uses classify_marker_era for era logic
- `scripts/bootstrap_doctor.py` — imports PLACEHOLDER_RE, SEMVER_RE, parse_bootstrap_marker, is_placeholder, classify_marker_era, find_placeholders from bootstrap_core; removed local duplicates; classify_era() delegates to classify_marker_era()
- `scripts/validate_bootstrap.py` — imports PLACEHOLDER_RE from bootstrap_core; added bootstrap_core.py + tests/test_bootstrap_core.py to BOOTSTRAP_REPO_REQUIRED_FILES
- `scripts/run_fixture_selftest.py` — imports PLACEHOLDER_RE from bootstrap_core

### Root
- `AGENTS.md` — added Shared bootstrap core and contract tests section; updated CI commands; updated forbidden actions; updated profile-expansion rule
- `CHANGELOG.md` — added 0.14.0 release entry for Milestone 17
- `IMPLEMENTATION_TRACKER.md` — this file; Milestone 17 recorded
- `README.md` — added Shared bootstrap core section; updated repository layout; updated CI table; updated local validation commands
- `VERSION` — bumped from 0.13.0 to 0.14.0

### CI
- `.github/workflows/ci.yml` — added bootstrap_core.py to syntax check; added contract test step

### Manifest
- `bootstrap-manifest.yaml` — added scripts/bootstrap_core.py and tests/test_bootstrap_core.py to bootstrap_repo_required_files

---

## Validation status (Milestone 17)

- `python scripts/validate_bootstrap.py` → PASSED (41 required files, 46 total checks)
- `python -m unittest discover -s tests -p 'test_*.py'` → 39 tests, 0 failures
- `python scripts/run_fixture_selftest.py` → B:PASS C:PASS D:PASS E:PASS F:PASS (both fixtures)

---

## Decisions made in Milestone 18 (doctor / audit contract test expansion)

| Decision | Reason | Alternative considered |
|----------|--------|----------------------|
| New `tests/test_bootstrap_doctor.py` for doctor-specific contract tests | Keep doctor semantics separate from core semantics; focused tests are easier to read and update | Appending to test_bootstrap_core.py (rejected: would mix core-helper tests with diagnosis-logic tests) |
| Test `_semver_tuple`, `_is_materially_behind`, and all status helpers directly | These are the key semantic units; unit-testing them directly catches bugs before they propagate | Only integration tests via audit() (rejected: harder to isolate which semantic broke) |
| Integration tests via `audit()` using real temp dirs | Proves the full pipeline end-to-end for key states; more realistic than mocking | Mocking internal calls (rejected: would hide integration bugs) |
| Scaffold test writes `{{BOOTSTRAP_NOTES}}` in marker | Accurately reflects real apply_bootstrap.py behavior: system fields are filled, `{{BOOTSTRAP_NOTES}}` is left for the agent | Marker with no placeholders (rejected: would not match actual scaffold-applied state) |
| No new health states or CLI changes | Milestone scope is proof and anti-drift, not feature expansion; existing six states are already well-specified | Adding new states (rejected: out of scope) |
| `test_bootstrap_doctor.py` added to BOOTSTRAP_REPO_REQUIRED_FILES in validate_bootstrap.py and manifest | Ensures future validate runs confirm the test file exists; consistent with treatment of test_bootstrap_core.py | Not adding (rejected: would leave a required asset untracked) |

---

## Files created/updated in Milestone 18 (doctor / audit contract test expansion)

### tests/ (new file)
- `tests/test_bootstrap_doctor.py` — new; 77 contract tests covering all six health states,
  version comparison helpers, marker/files/placeholder/profile-alignment status helpers,
  recommend_actions() for every state, era classification alignment with bootstrap_core,
  and audit() integration using real temporary directories

### scripts/ (updated)
- `scripts/validate_bootstrap.py` — added `tests/test_bootstrap_doctor.py` to
  `BOOTSTRAP_REPO_REQUIRED_FILES`

### Root
- `AGENTS.md` — added anti-drift rules to "Bootstrap doctor — advisory-only rules" section:
  diagnostic semantics are contract-tested; changes require test updates; output phrasing
  can vary but semantic meaning must not
- `IMPLEMENTATION_TRACKER.md` — this file; Milestone 18 recorded
- `README.md` — updated repository layout tree; expanded Contract tests section to document
  test_bootstrap_doctor.py coverage and doctor conservative behavior guarantee

### Manifest
- `bootstrap-manifest.yaml` — added `tests/test_bootstrap_doctor.py` to
  `bootstrap_repo_required_files`

---

## Validation status (Milestone 18)

- `python scripts/validate_bootstrap.py` → PASSED (42 required files, 47 total checks)
- `python -m unittest discover -s tests -p 'test_*.py'` → 120 tests, 0 failures
  (43 core contract tests + 77 doctor contract tests)
- `python scripts/run_fixture_selftest.py` → B:PASS C:PASS D:PASS E:PASS F:PASS (both fixtures)

---

## Known limitations (Milestone 18)

- Milestone 18 adds no new health states or CLI flags; all diagnosis semantics tested are
  those already present since Milestone 16.
- `profile-mismatch-review-recommended` integration test relies on the doctor's inline
  profile-scoring logic; not tested against the real `suggest_profile.py` subprocess.
  Cross-tool alignment is proven at the unit level (era/marker helpers) rather than by
  subprocess integration.
- No fixture for `stale-version-review-recommended` was added to State F; this state is
  covered by unit tests but not the end-to-end fixture harness (out of scope).

---

## Milestone 19 — Target Repo Audit JSON Schema Stabilization

**Objective:** Stabilize the machine-readable JSON contract for `bootstrap_doctor.py --json`
so downstream tooling can depend on it safely without coupling to human-readable text output.

**Files created:**
- `schemas/bootstrap_doctor_report.schema.json` — formal JSON Schema (draft-07) for doctor audit output

**Files updated:**
- `scripts/bootstrap_doctor.py` — added `DOCTOR_REPORT_SCHEMA_VERSION = "1.0.0"`,
  `_recommendations_to_structured()` helper, and updated `print_json_report()` to include
  `schema_version` and convert recommendations to structured objects (`{"type": "command"|"note", "value": "..."}`)
- `scripts/validate_bootstrap.py` — added `schemas/bootstrap_doctor_report.schema.json`
  to `BOOTSTRAP_REPO_REQUIRED_FILES` and `JSON_FILES_TO_VALIDATE`
- `bootstrap-manifest.yaml` — added new schema to `bootstrap_repo_required_files`
- `tests/test_bootstrap_doctor.py` — added 33 JSON contract tests across four new test classes:
  `TestJsonSchemaPresence`, `TestJsonReportShape`, `TestJsonReportFixtureStates`,
  `TestRecommendationsToStructured`
- `README.md` — added "Machine-readable JSON output contract" subsection with schema reference,
  stability guarantees table, and schema in directory listing
- `AGENTS.md` — added rules for JSON contract surface and schema/test update requirements

**JSON contract design chosen:**
- Schema version: `1.0.0` (independent field in JSON, separate from bootstrap repo version)
- Required fields: `schema_version`, `target_dir`, `bootstrapped`, `marker_status`,
  `marker_era`, `required_files_status`, `missing_files`, `placeholder_status`,
  `files_with_placeholders`, `total_placeholder_count`, `health_state`, `recommendations`
- Bounded enums for all classification fields
- Structured recommendations: `[{"type": "command"|"note", "value": "..."}]` — machine-parseable
  without string-matching; no `#`-prefixed comment strings in JSON output
- Optional fields: `recorded_version`, `source_version`, `recorded_profile`, `suggested_profile`,
  `profile_confidence`, `profile_alignment` (present but nullable)

**Versioning semantics:**
- `DOCTOR_REPORT_SCHEMA_VERSION` in `bootstrap_doctor.py` is the contract version
- patch: additive optional fields or clarifications
- minor: new required fields or enum additions
- major: renamed/removed required fields or semantically breaking changes

**Validation performed:**
- `python scripts/validate_bootstrap.py` → 43 files present, 49 checks passed
- `python -m unittest discover -s tests -p 'test_*.py' -v` → 153 tests, all passed
- `python scripts/run_fixture_selftest.py` → B:PASS C:PASS D:PASS E:PASS F:PASS for both fixtures
- `python scripts/bootstrap_doctor.py --target-dir <dir> --json` → conforms to schema with
  `schema_version`, structured recommendations, bounded enum values

**Known limitations (Milestone 19):**
- The JSON schema is not validated at runtime by `bootstrap_doctor.py` itself (no `jsonschema`
  dependency added — stdlib only). Schema conformance is proven by contract tests.
- `profile-mismatch-review-recommended` state not covered by `TestJsonReportFixtureStates`
  (fixture integration); covered by unit tests in prior milestone.
- Schema does not validate per-file details beyond list membership — deliberate to keep contract
  small and stable.

---

## Known limitations / follow-up opportunities

- `bootstrap_doctor.py` still carries its own inline profile-suggestion scoring (not imported from `suggest_profile.py`) — this was a pre-Milestone-17 design decision (Milestone 16) preserved for stability.
- `suggest_profile.py` uses a different `PROFILES` structure (signal-based) than `bootstrap_core.PROFILES` (template-based); the profile names must stay in sync manually. A follow-up could add a consistency check.
- No `__init__.py` or packaging — intentional; the scripts directory is not a package.
- The `stale-version-review-recommended` health state is covered by unit tests but not the end-to-end fixture harness; a future milestone could add a stale-version fixture state to State F for full end-to-end proof.

---

## Decisions made in Milestone 16 (target repo bootstrap doctor / audit mode)

| Decision | Reason | Alternative considered |
|----------|--------|----------------------|
| New standalone script (`bootstrap_doctor.py`) rather than extending existing scripts | Doctor is a distinct operational surface (read-only audit); adding it to validate or status would conflate different concerns | Extending bootstrap_status.py (rejected: status reports marker state, not full health classification) |
| Six health states (unbootstrapped, scaffold-applied-unpopulated, partially-populated, populated-and-healthy, stale-version-review-recommended, profile-mismatch-review-recommended) | Covers the practically distinct states an operator would encounter; maps cleanly to recommended actions without overlap | Fewer states (rejected: insufficient guidance); more states (deferred: YAGNI — adds complexity without clear operator benefit) |
| Profile suggestion logic duplicated inline rather than imported from suggest_profile.py | Avoids brittle inter-script coupling; doctor is self-contained; logic is short and consistent with the original | Importing or subprocess-calling suggest_profile.py (rejected: import coupling is fragile; subprocess adds complexity) |
| `--json` output for scripting, `--verbose` for detail, default human-readable | Consistent with suggest_profile.py pattern; operator-friendly by default | JSON-only (rejected: harder to read at command line) |
| Stale version defined as minor or major version difference (not patch) | Patch differences are safe and common; minor/major signal real template changes worth reviewing | Any version difference (rejected: patch-level noise would generate false refresh recommendations) |
| Profile mismatch recommendation only when confidence is high or medium | Low-confidence suggestions don't have enough evidence to override a recorded profile decision | Always recommend when profiles differ (rejected: would generate false positives on minimal fixtures) |
| State F doctor proof: raw=unbootstrapped, scaffold=scaffold-applied-unpopulated | These two states are the most important to prove; they cover the unbootstrapped and freshly-applied cases | Also proving populated-and-healthy (deferred: State C is already proven by validate; doctor proof in run_fixture_selftest.py covers the key states) |

---

## Files created/updated in Milestone 16 (target repo bootstrap doctor / audit mode)

### scripts/
- `scripts/bootstrap_doctor.py` — new; read-only target repo health audit tool
- `scripts/validate_bootstrap.py` — added `scripts/bootstrap_doctor.py` to `BOOTSTRAP_REPO_REQUIRED_FILES`
- `scripts/bootstrap_status.py` — added `scripts/bootstrap_doctor.py` to `CORE_SCRIPTS`
- `scripts/run_fixture_selftest.py` — added State F (doctor audit proof); added `run_doctor()` helper; updated summary output

### Root
- `AGENTS.md` — added fifth operational surface (doctor); added Bootstrap doctor advisory-only rules section; updated CI compile list
- `IMPLEMENTATION_TRACKER.md` — this file; Milestone 16 recorded
- `README.md` — added Bootstrap doctor section; updated repository layout

### CI
- `.github/workflows/ci.yml` — added `scripts/bootstrap_doctor.py` to syntax check step

---

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
| apply_bootstrap.py --profile generic (dry-run) | ✅ Pass | 7 files [CREATED]; profile line printed; exits 0 |
| apply_bootstrap.py --profile python-service | ✅ Pass | 7 files created; profile-specific AI_AGENT_VENDOR_KNOWLEDGE_BASE.md staged; exits 0 |
| apply_bootstrap.py --profile infra-repo | ✅ Pass | 7 files created; infra-specific variant staged; exits 0 |
| apply_bootstrap.py unknown profile | ✅ Pass | Exits 1 with clear error listing supported profiles |
| BOOTSTRAP_PROFILE auto-filled in marker | ✅ Pass | marker shows "python-service" after apply with that profile |
| refresh_bootstrap.py reads profile from marker | ✅ Pass | "Using profile: python-service" printed; profile-specific template used |
| refresh_bootstrap.py falls back to generic on no profile | ✅ Pass | "Using profile: generic" when marker has no Bootstrap profile row |
| validate_bootstrap.py detects 4 new profile template files | ✅ Pass | All 32 required files present; exits 0 |
| Self-test: minimal-python-service profile=python-service B:PASS C:PASS D:PASS | ✅ Pass | `python scripts/run_fixture_selftest.py` exits 0 |
| Self-test: minimal-infra-repo profile=infra-repo B:PASS C:PASS D:PASS | ✅ Pass | `python scripts/run_fixture_selftest.py` exits 0 |
| Full self-test (all fixtures, all states) | ✅ Pass | Both fixtures B:PASS C:PASS D:PASS |

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

## Files created/modified in Milestone 12 (manifest-driven bootstrap profiles)

### templates/profiles/ (new directory tree)
- `templates/profiles/python-service/docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template` — Python-service-specific guidance variant
- `templates/profiles/infra-repo/docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template` — IaC/infrastructure-specific guidance variant
- `templates/profiles/vscode-extension/docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template` — VS Code extension-specific guidance variant
- `templates/profiles/kubernetes-platform/docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template` — Kubernetes platform-specific guidance variant

### templates/bootstrap/
- `templates/bootstrap/BOOTSTRAP_SOURCE.md.template` — added `Bootstrap profile` row; updated comment block

### scripts/
- `scripts/apply_bootstrap.py` — added `PROFILES` dict; added `--profile` flag (default: `generic`); added `resolve_mappings()`; extended `render_marker()` to fill `{{BOOTSTRAP_PROFILE}}`; updated `main()` to use profile-aware mappings and print profile info
- `scripts/refresh_bootstrap.py` — added `PROFILES` dict and `DEFAULT_PROFILE`; added `resolve_mappings()`; extended `detect_bootstrap_state()` to parse `Bootstrap profile` from marker; extended `render_marker()` to fill `{{BOOTSTRAP_PROFILE}}`; updated `main()` to read profile from marker and use profile-aware mappings
- `scripts/validate_bootstrap.py` — added 4 profile template files to `BOOTSTRAP_REPO_REQUIRED_FILES`
- `scripts/run_fixture_selftest.py` — added `FIXTURE_PROFILES` dict; updated `run_apply()` to accept `profile` parameter; updated `test_fixture()` to pass the fixture's profile to apply

### Root
- `AGENTS.md` — updated operational surface 2 (apply) to show `--profile`; added `## Bootstrap profiles` section with profile rules; added profile restriction to forbidden actions
- `IMPLEMENTATION_TRACKER.md` — this file; Milestone 12 recorded
- `bootstrap-manifest.yaml` — added 4 profile template files to `bootstrap_repo_required_files`; added `BOOTSTRAP_PROFILE` to `auto_filled_placeholders`; added `profile:` field to fixture entries; added `## profiles:` section with all 5 profile definitions and template_overrides
- `README.md` — added `## Bootstrap profiles` section; updated repository layout to show `templates/profiles/`; updated quick-start to show `--profile` example

---

## Milestone 13 — Versioned Bootstrap Releases and Compatibility / Upgrade Policy

### Objective
Establish a minimal, durable versioning and compatibility model so maintainers and
target repositories can reliably answer: what version is this, what changed, and
when is refresh safe.

### Versioning design chosen
- **Single source of truth**: `VERSION` file at repo root containing a semver string.
  Chosen over a manifest field because it is simpler to read, human-readable, and
  easy to bump without YAML parsing knowledge.
- **Marker fields**: `Bootstrap source version` records the semver version;
  `Bootstrap source revision` records the git SHA as supplemental traceability.
- **Major-version drift warning**: `refresh_bootstrap.py` warns when the target's
  recorded major version differs from the current bootstrap major version.

### Marker/compatibility decisions
- `BOOTSTRAP_SOURCE_VERSION` now records the semver version (changed from git SHA).
- `BOOTSTRAP_SOURCE_REVISION` is a new auto-filled field for the git SHA.
- Pre-version markers (git SHA in version field) are treated as pre-0.13.0.
- All changes are backward-compatible: refresh still classifies markers correctly.

### Files created in Milestone 13

#### Root
- `VERSION` — new; single source of truth for bootstrap version (`0.13.0`)
- `CHANGELOG.md` — new; first formalized changelog with 0.13.0 entry and pre-release history

#### docs/
- `docs/BOOTSTRAP_VERSIONING.md` — new; compatibility/upgrade policy document

#### scripts/ (modified)
- `scripts/apply_bootstrap.py` — added `read_bootstrap_version()`; changed version source
  from git SHA to VERSION file; added `bootstrap_revision` (git SHA) to ctx; updated
  `render_marker()` to fill `{{BOOTSTRAP_SOURCE_REVISION}}`; updated output labels
- `scripts/refresh_bootstrap.py` — added `read_bootstrap_version()` and
  `parse_major_version()`; changed version source to VERSION file; added `bootstrap_revision`;
  updated `render_marker()` to fill `{{BOOTSTRAP_SOURCE_REVISION}}`; added major-version
  drift warning in `main()`; updated `--bootstrap-version` help text
- `scripts/validate_bootstrap.py` — added `VERSION`, `CHANGELOG.md`,
  `docs/BOOTSTRAP_VERSIONING.md` to `BOOTSTRAP_REPO_REQUIRED_FILES`; added
  `check_version_file()` function; added version check call in bootstrap source validation

#### templates/
- `templates/bootstrap/BOOTSTRAP_SOURCE.md.template` — added `Bootstrap source revision`
  row; updated comment block for new field semantics

#### Root (modified)
- `AGENTS.md` — added `## Version discipline` section with version bump rules
- `IMPLEMENTATION_TRACKER.md` — this file; Milestone 13 recorded
- `bootstrap-manifest.yaml` — removed `bootstrap_version` field (replaced with a comment pointing to VERSION as the authoritative source); added new required files
- `README.md` — added `## Bootstrap versioning` section

### Validation performed
- `python scripts/validate_bootstrap.py` → PASSED (39 checks)
- `python scripts/run_fixture_selftest.py` → PASSED (B:PASS C:PASS D:PASS for both fixtures)
- Manual verification: `apply_bootstrap.py` marker shows correct semver version and git SHA
- Manual verification: `refresh_bootstrap.py` shows prior/current version comparison
- Manual verification: major-version drift warning triggered correctly

### Known limitations (Milestone 13)
- No automated git tagging or GitHub Releases integration — intentionally out of scope.
- The PROFILES dict in `apply_bootstrap.py` and `refresh_bootstrap.py` remains duplicated
  (not related to versioning; deferred from Milestone 12).

---

## Milestone 14 — Release Discipline and Bootstrap Status / Report Mode

**Date:** 2026-03-14  
**Status:** Complete

### Objective

Add a small operational layer for inspecting bootstrap repo release state,
inspecting target repo bootstrap markers, validating version/changelog coherence,
and following a repeatable release checklist.

### Files created

- `scripts/bootstrap_status.py` — new status/report script (source repo and target
  repo modes, version/changelog coherence check, profile list)
- `docs/BOOTSTRAP_RELEASE_WORKFLOW.md` — concise release checklist and workflow doc

### Files updated

- `scripts/validate_bootstrap.py` — added `check_changelog_coherence()` and
  `check_version_file()` now returns the version string; changelog coherence
  check added as Check 4 in source repo validation; added new required files
  (`docs/BOOTSTRAP_RELEASE_WORKFLOW.md`, `scripts/bootstrap_status.py`)
- `bootstrap-manifest.yaml` — added `docs/BOOTSTRAP_RELEASE_WORKFLOW.md` and
  `scripts/bootstrap_status.py` to `bootstrap_repo_required_files`
- `.github/workflows/ci.yml` — added `scripts/bootstrap_status.py` to py_compile step
- `README.md` — added `## Bootstrap status and release workflow` section
- `AGENTS.md` — added `## Release discipline` section
- `IMPLEMENTATION_TRACKER.md` — this file; Milestone 14 recorded

### Status/report design chosen

Single script `scripts/bootstrap_status.py` with two modes:
1. **Source repo mode** (default): reports version, git revision, CHANGELOG,
   core docs, core scripts, profiles, and version/changelog coherence.
2. **Target repo mode** (`--target-dir`): parses `bootstrap/BOOTSTRAP_SOURCE.md`
   and reports all marker fields, era classification, and profile.

### Coherence checks added

In `scripts/validate_bootstrap.py`:
- `check_changelog_coherence()`: verifies that the current version from `VERSION`
  appears as a release heading in `CHANGELOG.md`, OR that an `[Unreleased]` section
  exists. Fails only on clear incoherence.

In `scripts/bootstrap_status.py`:
- Same coherence logic in human-readable form, surfaced in source repo status output.

### Validation performed

- `python scripts/validate_bootstrap.py` → PASSED (42 checks, up from 39)
- `python scripts/run_fixture_selftest.py` → PASSED (B:PASS C:PASS D:PASS for both fixtures)
- `python scripts/bootstrap_status.py` → source repo status reported correctly
- `python scripts/bootstrap_status.py --target-dir /tmp/test_target` → marker parsed
  and reported correctly for a populated marker
- `python scripts/bootstrap_status.py --target-dir /tmp/missing` → missing marker
  reported clearly without crashing

### Known limitations (Milestone 14)

- `bootstrap_status.py` reads profiles via a simple line scan of the manifest YAML;
  does not use a YAML parser (by design, to stay dependency-free). Works reliably for
  the current manifest structure.
- No JSON export or machine-readable output from `bootstrap_status.py` — intentional;
  kept human-readable per milestone scope.
- No automated git tagging or GitHub Releases integration — out of scope.

---

## Milestone 15 — Profile Suggestion / Repo Classification Report Mode

**Objective:** Add a read-only profile suggestion tool that inspects a target repository
and recommends the most likely bootstrap profile based on file-system evidence.

**Script chosen:** New script `scripts/suggest_profile.py` (preferred over extending
`bootstrap_status.py` — keeps concerns separated and the suggestion logic self-contained).

**Heuristic design:**
- Each profile has an explicit list of named signals with `check(target_dir) -> bool` callables.
- Signals have weights (1 or 2) based on how strongly they indicate a profile.
- Score is sum of matched weights; confidence is `high` (≥65%), `medium` (≥35%), `low`.
- If top score is 0, falls back to `generic` with low confidence.
- No ML, no opaque scoring — all logic is readable in `PROFILES` dict.

**Files created:**
- `scripts/suggest_profile.py` — the new read-only suggestion tool

**Files updated:**
- `scripts/run_fixture_selftest.py` — added State E (profile suggestion proof for each fixture)
- `scripts/validate_bootstrap.py` — added `suggest_profile.py` to required files
- `scripts/bootstrap_status.py` — added `suggest_profile.py` to CORE_SCRIPTS list
- `bootstrap-manifest.yaml` — added `suggest_profile.py` to `bootstrap_repo_required_files`
- `README.md` — added "Profile suggestion" section
- `AGENTS.md` — added "Profile suggestion — advisory-only rules" section

**Validation performed:**
- `python scripts/validate_bootstrap.py` → 38 files present, 43 checks passed
- `python scripts/run_fixture_selftest.py` → B:PASS C:PASS D:PASS E:PASS for both fixtures
  - minimal-python-service → suggested `python-service` (high confidence) ✓
  - minimal-infra-repo → suggested `infra-repo` (medium confidence) ✓
- `python scripts/suggest_profile.py --target-dir <dir> --verbose` → correct output
- `python scripts/suggest_profile.py --target-dir <dir> --json` → valid JSON output
- `python scripts/suggest_profile.py --target-dir /nonexistent` → exits 1 with clear error

**Known limitations (Milestone 15):**
- `infra-repo` achieves medium (not high) confidence on the minimal-infra-repo fixture
  because the fixture lacks `.tf` files (the strongest infra signal). This is honest —
  the fixture is minimal by design.
- No fixtures for `vscode-extension` or `kubernetes-platform` exist yet; suggestion
  correctness for those profiles is unproven by fixture (out of scope for this milestone).
- Suggestion is based entirely on file-system structure; no content parsing beyond
  simple `str.lower() in content` substring checks.

---

## Open improvements (future milestones)

- [x] Add `--target-dir` mode to `validate_bootstrap.py` to validate a bootstrapped target repo ✅ Done (Milestone 7)
- [x] Add `scripts/apply_bootstrap.py` to stage scaffold into target repos safely ✅ Done (Milestone 8)
- [x] Add end-to-end fixture self-test harness ✅ Done (Milestone 9)
- [ ] Add a `jsonschema`-based validation mode (optional, behind `--strict` flag)
- [x] Add a GitHub Actions workflow to run `validate_bootstrap.py` and `run_fixture_selftest.py` on push ✅ Done (Milestone 10)
- [x] Add a safe refresh/upgrade path for already-bootstrapped target repos ✅ Done (Milestone 11)
- [x] Add manifest-driven bootstrap profiles ✅ Done (Milestone 12)
- [x] Add versioned bootstrap releases and compatibility/upgrade policy ✅ Done (Milestone 13)
- [x] Add release discipline and bootstrap status/report mode ✅ Done (Milestone 14)
- [x] Add profile suggestion / repo classification report mode ✅ Done (Milestone 15)
- [ ] Expand examples with concrete file trees and discovery findings
- [ ] Add a `prompts/target-repo-audit.md` for ongoing maintenance sessions
- [x] Add a `CHANGELOG.md` when this repo has meaningful version history ✅ Done (Milestone 13)
- [ ] Add CODEOWNERS or similar if this becomes a shared team resource
- [ ] Make `apply_bootstrap.py` and `refresh_bootstrap.py` fully read template mappings
  from `bootstrap-manifest.yaml` rather than the static fallback list (currently in sync;
  unifying reduces future drift)
- [ ] Add profile-specific fixture proof data for vscode-extension and kubernetes-platform

---

## Known limitations (Milestone 14)

See "Known limitations" above under the Milestone 14 entry.

---

## Next strongest bounded milestone

**Milestone 20 — CHANGELOG and VERSION bump for Milestone 19**

Update CHANGELOG.md and VERSION to reflect the Milestone 19 release (JSON schema stabilization).

Scope:
- Bump VERSION to `0.16.0` (minor bump: new schema file, new required field `schema_version` in JSON output)
- Update CHANGELOG.md with Milestone 19 release notes
- Keep the existing release workflow

Estimated size: Minimal (2 files: `VERSION`, `CHANGELOG.md`)
