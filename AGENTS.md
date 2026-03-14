# AGENTS.md — Execution Contract for agent-bootstrap

This file is the operating contract for AI agents working **in this repository**.  
Read it before taking any action. Deviate from it only with explicit justification recorded in `IMPLEMENTATION_TRACKER.md`.

---

## Repo mission

This repository is the canonical source of truth for bootstrapping AI-agent-assisted projects.  
It provides prompts, templates, schemas, and a validation script that agents use to initialize and operate target repositories.

It is **not** a target repo. Do not add project-specific content here.

---

## Scope of this repository

In scope:
- Prompt files for common agent workflows
- Templates for required target-repo operating files
- JSON schemas for structured artifacts
- A lightweight validation script
- A scaffold apply script for staging templates into target repos
- End-to-end fixture target repos and self-test harness
- Documentation explaining the system
- The implementation tracker for this repo's own state

Out of scope:
- Target-repo-specific content
- Full CLI tooling or package publishing
- CI/CD automation beyond what is required to validate bootstrap files
- Language-specific application code

---

## Operational surfaces

This repository has five operational surfaces:

1. **Bootstrap source validation** — confirms that this repo's own required files
   are present and intact.
   ```
   python scripts/validate_bootstrap.py
   ```

2. **Target repo scaffold application** — stages canonical template files into a
   target repository so an agent can populate them with real, evidence-based content.
   Supports optional `--profile` to select a profile-specific template variant.
   ```
   python scripts/apply_bootstrap.py --target-dir /path/to/target-repo
   python scripts/apply_bootstrap.py --target-dir /path/to/target-repo --profile python-service
   ```

3. **Target repo refresh / upgrade** — updates managed files in an already-bootstrapped
   target repository to align with the current canonical templates. Safe by default:
   skips populated files unless `--force` is given.
   ```
   python scripts/refresh_bootstrap.py --target-dir /path/to/target-repo --dry-run
   python scripts/refresh_bootstrap.py --target-dir /path/to/target-repo
   ```

4. **End-to-end fixture self-test** — applies the scaffold to controlled fixture
   target repos and validates the result, proving the apply and validate paths work.
   ```
   python scripts/run_fixture_selftest.py
   ```

5. **Target repo health audit (doctor mode)** — read-only diagnostic tool that
   inspects a target repository and reports its bootstrap health, drift, and
   recommended next action. Never mutates any file.
   ```
   python scripts/bootstrap_doctor.py --target-dir /path/to/target-repo
   python scripts/bootstrap_doctor.py --target-dir /path/to/target-repo --verbose
   python scripts/bootstrap_doctor.py --target-dir /path/to/target-repo --json
   ```

The apply and refresh scripts are both **safe by default**: they never overwrite
populated files unless `--force` is passed explicitly. Always run with `--dry-run`
first when unsure.

Target-repo content population (filling `{{PLACEHOLDER}}` markers) remains
**agent-led and evidence-driven**. Neither script auto-fills repo-specific content.
Run the appropriate prompt after apply.

---

## Target repo lifecycle

Target repositories now have a lifecycle, not just an initial bootstrap:

1. **Apply** (`apply_bootstrap.py`) — create the scaffold in a fresh target repo.
2. **Populate** (agent session with a prompt) — fill placeholders with real evidence.
3. **Validate** (`validate_bootstrap.py --target-dir`) — confirm the populated state.
4. **Refresh** (`refresh_bootstrap.py`) — realign managed files when bootstrap templates
   are updated.

Agents operating on bootstrapped target repos must respect this lifecycle:
- Do not treat refresh as an opportunity to clobber populated repo-specific files.
- Diagnose diffs and local edits before deciding to force an overwrite.
- Prefer `--dry-run` output as a diagnostic tool before taking action.
- Any template or manifest change must preserve safe upgrade behavior.

**Repo-specific populated files must not be overwritten casually.**
The `IMPLEMENTATION_TRACKER.md`, `artifacts/ai/repo_discovery.json`, and similar
files contain real project state. Treat them as authoritative unless there is
explicit evidence they should be replaced.

---

## Authoritative files

These files define the state and rules of this repository:

| File | Role |
|------|------|
| `AGENTS.md` | This file — execution contract |
| `IMPLEMENTATION_TRACKER.md` | Live state, milestones, decisions |
| `bootstrap-manifest.yaml` | Machine-readable control plane |
| `README.md` | Human-readable overview |

When in doubt about intent, consult these files in order.

---

## Forbidden actions

Do not:
- Add target-repo-specific content to this repository.
- Invent project history, decisions, or context not supported by evidence.
- Fill templates with fake or made-up repo-specific data.
- Add dependencies (pip, npm, etc.) unless clearly required and recorded.
- Remove or rename authoritative files without updating all cross-references.
- Mark milestones complete in the tracker without actually completing the work.
- Create speculative architecture or aspirational code that is not functional.
- Silently change the semantics of prompt files.
- Blindly overwrite populated target-repo files during refresh — always classify first.
- Change apply, refresh, or validation logic in ways that break safe-by-default behavior.
- Add new profiles without updating all locations: `PROFILES` in `bootstrap_core.py`, `bootstrap-manifest.yaml`, required-files list in `validate_bootstrap.py`, and fixture/validation proof.

---

## Change discipline

Before making any change:
1. Confirm the change is within the declared milestone scope.
2. Record the reason in `IMPLEMENTATION_TRACKER.md` if it is a significant decision.
3. Update all cross-references (README layout, manifest, tracker) if adding or renaming a file.

After making any change:
1. Update `IMPLEMENTATION_TRACKER.md` with the file and status.
2. Verify internal references (e.g., README layout matches actual file tree).
3. Run `scripts/validate_bootstrap.py` if structural files were added or removed.

---

## Validation expectations

Every agent session touching this repo must:
- Confirm required files exist before declaring work complete.
- Run `python scripts/validate_bootstrap.py` and record the result.
- Note any validation gaps in the tracker under "Validation Status."

Validation does **not** require semantic correctness of templates — only file presence and basic structure.

---

## Fixture and self-test rules

Fixtures in `fixtures/` are regression-proof assets. Handle them carefully.

Rules:
- Fixtures must remain intentionally minimal. Do not add unnecessary files.
- Fixture edits must be intentional and documented in `IMPLEMENTATION_TRACKER.md`.
- `fixtures/population/*.json` must cover all `{{PLACEHOLDER}}` markers in the
  templates. Update population data whenever templates change.
- The self-test harness must pass after any change to templates, prompts, apply
  logic, or validation logic. Run it before declaring milestone work complete:
  ```
  python scripts/run_fixture_selftest.py
  ```
- Fixture population data is **proof-only**. It is not real discovery content.
  Never present it as evidence of actual repository analysis.
- The self-test harness must never mutate canonical fixture directories.
  All operations must use working copies.
- Prefer extending proof coverage carefully over adding new fixtures casually.
  New fixtures should represent a meaningfully different repo shape.

---

## CI regression gate

`.github/workflows/ci.yml` is the automated regression gate for this repository.
It runs on pull requests, pushes to `main`, and manual dispatch (`workflow_dispatch`).
Feature-branch pushes do not independently trigger the workflow; they are covered by the `pull_request` event.

Rules:
- CI is required. Do not bypass or disable it.
- Any change to prompts, templates, manifest, scripts, or fixtures must leave CI passing.
- If CI fails after your change, diagnose the root cause. Do not paper over failures
  with superficial workarounds or by weakening the checks.
- Keep the workflow lean and readable. Do not add heavyweight tooling, large matrices,
  or packaging/release steps to the CI workflow.
- If a CI failure is pre-existing and unrelated to your change, record it in
  `IMPLEMENTATION_TRACKER.md` as a known gap rather than silently ignoring it.

The workflow runs these commands in order:
```
python -m py_compile scripts/validate_bootstrap.py scripts/apply_bootstrap.py scripts/run_fixture_selftest.py scripts/refresh_bootstrap.py scripts/bootstrap_status.py scripts/suggest_profile.py scripts/bootstrap_doctor.py scripts/bootstrap_core.py
python scripts/validate_bootstrap.py
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/run_fixture_selftest.py
```

Before pushing, run these same commands locally to avoid CI surprises.

---

Templates live in `templates/`. They are canonical starting points for target repos.

Rules:
- Use `{{PLACEHOLDER}}` style markers for content that must be filled from real evidence.
- Do not fill placeholders with invented data.
- Include a header comment in each template explaining its purpose.
- Keep structure clear enough that a future agent can fill it without this chat context.
- Every template must have at least: a title, a purpose statement, and placeholders for key fields.

---

## Shared bootstrap core and contract tests

`scripts/bootstrap_core.py` is the single source of truth for shared bootstrap semantics.

### Rules for agents

- **Shared semantics belong in `bootstrap_core.py`, not reimplemented ad hoc.**
  When adding new semantic logic that is used (or likely to be used) by more than one
  script, add it to the core, not to each script independently.

- **User-facing scripts should consume shared helpers where practical.**
  `apply_bootstrap.py`, `refresh_bootstrap.py`, `bootstrap_status.py`,
  `bootstrap_doctor.py`, `validate_bootstrap.py`, and `run_fixture_selftest.py`
  import from `bootstrap_core`.  Keep that pattern.

- **Script-specific output and CLI logic stays in each script.**
  Do not move output formatting, argument parsing, or script-specific control flow
  into the core. The core is for pure semantic helpers only.

- **Contract tests must be updated alongside meaningful changes to shared semantics.**
  `tests/test_bootstrap_core.py` proves the stability of the core's public helpers.
  If you add or change a helper in the core, add or update the corresponding test.

- **Keep the core small.**
  If a piece of logic is only used by one script and is unlikely to be reused, leave
  it in that script. Prefer consolidation of confirmed-duplicate logic over
  preemptive abstraction.

- **Future refactors should prefer drift reduction over clever architecture.**
  The goal is that a fix to a shared semantic (e.g., marker field name, era
  classification rule) happens in one place and all scripts benefit automatically.

- **The `PROFILES` dict in `bootstrap_core.py` is authoritative.**
  `apply_bootstrap.py` and `refresh_bootstrap.py` import it.  `suggest_profile.py`
  maintains its own signal dict (heuristic, not structural) but the profile names
  it references must match the core's `PROFILES` keys.

---

## Bootstrap profiles

Profiles provide bounded scaffold shape variation for different target-repo families.
They are implemented as manifest-driven template overlays — a small and explicit mechanism.

### Profile rules for agents

- **Profiles are bounded overlays, not permission to guess repo facts.**
  A profile selects which template variant to stage. It does not auto-populate
  repo-specific content. All `{{PLACEHOLDER}}` markers remain for agent population.

- **Common/core bootstrap behavior is authoritative and applies to all profiles.**
  Profile overrides are a narrow exception for templates where family-specific guidance
  materially improves usefulness (currently: `AI_AGENT_VENDOR_KNOWLEDGE_BASE.md`).

- **Profile additions must stay small and explicit.**
  Add a new profile template only if it provides clearly distinct and useful guidance.
  Do not create profile variants that duplicate the generic template with trivial changes.

- **Future profile expansion must preserve CI/self-test coverage.**
  Any new profile must be added to `PROFILES` in `bootstrap_core.py` (the single
  authoritative source), `apply_bootstrap.py` and `refresh_bootstrap.py` import from
  the core automatically.  Also update `bootstrap-manifest.yaml`, add the template
  to `BOOTSTRAP_REPO_REQUIRED_FILES` in `validate_bootstrap.py`, and prove it
  through a fixture or explicit validation run before declaring it operational.

- **Prefer extending manifest mappings over ad hoc special cases in scripts.**
  Profile logic lives in the `PROFILES` dict (scripts) and the `profiles:` section (manifest).
  Do not scatter profile-conditional logic across unrelated parts of the codebase.

- **The apply script must always fail clearly on an unknown profile.**
  Do not silently fall back to `generic` on an unrecognised profile at apply time.
  Refresh may fall back to `generic` with a warning if the marker records an unknown profile.

---

## Profile suggestion — advisory-only rules

`scripts/suggest_profile.py` is a read-only heuristic classifier.  
It inspects a target repo and suggests the most likely profile.  
Agents must understand and respect the following contract:

- **Profile suggestion is advisory only.**
  The script produces a recommendation for the maintainer. It does not apply anything,
  write any files, or make any decisions on behalf of the operator.

- **Apply must remain explicit.**
  `apply_bootstrap.py` must never auto-select a profile based on suggestion output.
  The operator always provides `--profile` explicitly. Do not change this.

- **Heuristics must stay small and evidence-based.**
  Signal rules live in `PROFILES` dict in `suggest_profile.py`. Each signal must have
  a clear, inspectable check. Avoid clever scoring abstractions that obscure reasoning.

- **Weak evidence must fall back honestly to `generic`.**
  If no profile scores above zero, or evidence is mixed and no clear winner exists,
  the tool must report `generic` and say so explicitly. Never invent confidence.

- **Future profile additions must include suggestion logic.**
  When adding a new profile, add corresponding signals to `PROFILES` in `suggest_profile.py`
  and add an expected profile entry in `FIXTURE_EXPECTED_PROFILES` in `run_fixture_selftest.py`
  if a fixture for that profile exists. Do not add a new profile without proof coverage.

- **The suggestion tool must never mutate the target repo.**
  No file writes, no subprocess calls that modify state. Read-only filesystem inspection only.

---

## Bootstrap doctor — advisory-only rules

`scripts/bootstrap_doctor.py` is a read-only diagnostic tool.
It inspects a target repo and reports its bootstrap health, drift, and recommended next action.
Agents must understand and respect the following contract:

- **The doctor is advisory and read-only.**
  It produces a health report and recommendations for the operator.
  It never applies scaffolds, runs refresh, or mutates any file.

- **Diagnostic states must stay small and stable.**
  The six health states are the stable vocabulary for describing target-repo health.
  Do not add new states without a clear, justified need.
  Do not rename existing states without a semver minor version bump.

- **Recommendations must remain conservative.**
  The doctor recommends `--dry-run` first, then the actual command.
  It never recommends `--force` by default.
  It never auto-runs apply, refresh, or validate.

- **Future additions should prefer explicit operator guidance over automation.**
  The doctor's job is to surface information clearly, not to make decisions on behalf of the operator.
  If adding new checks, keep them read-only and evidence-based.

- **Fixture proof is required for new health state branches.**
  If a new health state is added, add it to `FIXTURE_EXPECTED_DOCTOR_STATES` in
  `run_fixture_selftest.py` and prove its classification against a fixture state.

- **The doctor must never shell out to external processes.**
  All checks use direct filesystem inspection. No subprocess calls.

- **Diagnostic semantics are contract-tested and must not drift casually.**
  `tests/test_bootstrap_doctor.py` proves all six health state classifications,
  version comparison helpers, profile alignment, placeholder/required-file status,
  and recommended next-action guidance.  Changes to any of these behaviors require
  corresponding test updates — output phrasing can vary, but semantic meaning must not.

- **Changes to doctor/status/suggest shared meaning require test updates.**
  `classify_era()` in bootstrap_doctor delegates to `bootstrap_core.classify_marker_era()`.
  `parse_marker()` delegates to `bootstrap_core.parse_bootstrap_marker()`.
  If either shared helper changes, update both `test_bootstrap_core.py` and
  `test_bootstrap_doctor.py`.  Anti-drift hardening is preferred over feature sprawl.

---

Prompts live in `prompts/`. They are copy-paste-ready instructions for agent sessions.

Rules:
- Each prompt must begin with a clear statement of its purpose and scope.
- Prompts must enforce inspection before change.
- Prompts must require evidence-based updates (no guessing).
- Prompts must include explicit stop conditions.
- Prompts must require tracker and documentation updates.
- Do not write vague or aspirational prompts — write operational ones.

---

## Schema rules

Schemas live in `schemas/`. They are JSON Schema files.

Rules:
- Schemas must be valid JSON Schema (draft-07 or later).
- Use `"additionalProperties": false` only where strictness is clearly beneficial.
- Prefer `"required"` for fields an agent must always populate.
- Keep schemas practical — validate shape, not business logic.
- Do not add computed or runtime-only fields.

---

## Version discipline

The bootstrap version is defined in the `VERSION` file at the repository root.
Version bumps are **deliberate decisions**, not incidental edits.

Rules:
- Do not change `VERSION` without also updating `CHANGELOG.md`.
- Do not update `CHANGELOG.md` without also updating `VERSION` (unless adding to `[Unreleased]`).
- Marker structure changes (field additions/renames/removals) require a version bump.
  - Additive changes → minor bump.
  - Breaking changes (rename/remove) → major bump.
- Patch bumps are for documentation, template copy, and script bug fixes that do not
  change marker structure or refresh behavior.
- The `BOOTSTRAP_SOURCE_VERSION` and `BOOTSTRAP_SOURCE_REVISION` fields in the marker
  are part of the contract — do not remove or rename them without a major version bump.
- Refresh behavior must remain compatible with the documented policy in
  `docs/BOOTSTRAP_VERSIONING.md`. Any change to refresh safety semantics requires
  updating both the policy doc and the version.
- Pre-version markers (those with a git SHA or empty value in `Bootstrap source version`)
  should be treated as pre-0.13.0. Do not assume their profile or structure.
- Changelog updates should accompany meaningful version changes. For trivial fixes,
  adding to the `[Unreleased]` section is sufficient until the next release.

---

## Release discipline

Release discipline is part of the operating contract for this repository.

Rules:
- Before merging any release-oriented change, run the full local pre-release
  checklist in `docs/BOOTSTRAP_RELEASE_WORKFLOW.md`.
- `scripts/bootstrap_status.py` is the fast operator check for source and target
  repo state. Run it when inspecting bootstrap state. Keep it lean and human-readable.
- Status/report tooling must remain dependency-free (standard library only) and
  produce plain human-readable output. Do not add JSON export, dashboards, or
  external integrations.
- Future CI or release enhancements must preserve simplicity. Do not add release
  automation, tag-pushing, or publish steps to CI without an explicit decision.
- When adding new required files, update both `BOOTSTRAP_REPO_REQUIRED_FILES` in
  `validate_bootstrap.py` and `bootstrap_repo_required_files` in
  `bootstrap-manifest.yaml` together. The CI gate will catch drift.

---

## How to handle uncertainty

When uncertain about intent:
1. Consult `bootstrap-manifest.yaml` for required behaviors.
2. Consult `IMPLEMENTATION_TRACKER.md` for prior decisions.
3. If still uncertain, record the uncertainty explicitly in the tracker rather than guessing.
4. Do not invent context. Label recommendations as recommendations.

---

## Commit discipline

Commit at milestone boundaries. Each commit message must:
- Identify the milestone.
- List the files changed.
- Be written in present tense, imperative mood.

Example: `Add Milestone 3 prompt files: new-repo-bootstrap, resume-work, bounded-implementation`

Do not mix milestone work in a single commit unless the changes are trivially small.

---

## Loop-breaking expectations

If you find yourself:
- Repeating the same failed approach more than twice: stop and choose a simpler path.
- Unable to populate a template with real evidence: leave the placeholder and record the gap.
- Blocked on a file that does not exist yet: create a minimal stub and record it as incomplete.

Prefer stable scaffolding over cleverness.  
Record every loop-break decision in `IMPLEMENTATION_TRACKER.md`.
