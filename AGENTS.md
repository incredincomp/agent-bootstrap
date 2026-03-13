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

This repository has three operational surfaces:

1. **Bootstrap source validation** — confirms that this repo's own required files
   are present and intact.
   ```
   python scripts/validate_bootstrap.py
   ```

2. **Target repo scaffold application** — stages canonical template files into a
   target repository so an agent can populate them with real, evidence-based content.
   ```
   python scripts/apply_bootstrap.py --target-dir /path/to/target-repo
   ```

3. **End-to-end fixture self-test** — applies the scaffold to controlled fixture
   target repos and validates the result, proving the apply and validate paths work.
   ```
   python scripts/run_fixture_selftest.py
   ```

The apply script is **safe by default**: it never overwrites existing files unless
`--force` is passed explicitly. Always run with `--dry-run` first when unsure.

Target-repo content population (filling `{{PLACEHOLDER}}` markers) remains
**agent-led and evidence-driven**. The apply script does not auto-fill repo-specific
content. Run the appropriate prompt after apply.

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



Templates live in `templates/`. They are canonical starting points for target repos.

Rules:
- Use `{{PLACEHOLDER}}` style markers for content that must be filled from real evidence.
- Do not fill placeholders with invented data.
- Include a header comment in each template explaining its purpose.
- Keep structure clear enough that a future agent can fill it without this chat context.
- Every template must have at least: a title, a purpose statement, and placeholders for key fields.

---

## Prompt-writing rules

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
