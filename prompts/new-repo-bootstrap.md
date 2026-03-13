# Prompt: New Repository Bootstrap

**Purpose:** Initialize a brand-new or mostly undocumented target repository with the full set of AI agent operating files.

**When to use:** The target repo has no `AGENTS.md`, no `IMPLEMENTATION_TRACKER.md`, and no `docs/ai/` directory, or it is essentially empty.

**Scope:** Discovery + creation of all required operating files. Do not implement features or refactor existing code during this run.

---

## Instructions

You are bootstrapping a target repository. Follow each step in order. Do not skip steps. Do not make assumptions without evidence.

---

### Step 1 — Locate the bootstrap source

Before touching the target repo, confirm you have access to the `agent-bootstrap` source repository (or the files extracted from it). You will need:
- `bootstrap-manifest.yaml` — defines required outputs and stop conditions
- `templates/` — canonical templates to populate
- `schemas/` — JSON schemas for validation
- `scripts/validate_bootstrap.py` — validation script

If any of these are unavailable, stop and record the gap before proceeding.

---

### Step 2 — Inspect the target repository

**Do this before creating any files.**

Collect evidence on:
- Directory structure (top-level and key subdirectories)
- Primary language(s) and build system
- Package manager and dependency files
- Existing documentation (README, docs/, wikis)
- Existing CI/CD configuration
- Existing agent-operating files (AGENTS.md, IMPLEMENTATION_TRACKER.md, docs/ai/)
- Deployment model (if determinable from config files)
- Test framework and test directory structure
- Any non-obvious entry points or authoritative config files

Record all findings. You will need them to fill the templates.

**Stop condition for this step:** You can answer all of the following:
1. What language(s) is this repo written in?
2. How is it built and tested?
3. Are any operating files already present?
4. What are the authoritative configuration files?

---

### Step 3 — Create `artifacts/ai/repo_discovery.json`

Using your findings from Step 2, populate the discovery artifact.
- Use `templates/artifacts/ai/repo_discovery.json.template` as the starting point.
- Fill every field with real evidence. Where a field is genuinely unknown, use `null` and add a note in `discovery_notes`.
- Validate against `schemas/repo_discovery.schema.json` if available.
- Do not invent data.

---

### Step 4 — Create `bootstrap/BOOTSTRAP_SOURCE.md`

Record where this bootstrap originated.
- Use `templates/bootstrap/BOOTSTRAP_SOURCE.md.template`.
- Include: source repo, date, agent identity (if known), and a brief summary of what was created.

---

### Step 5 — Create `AGENTS.md`

Create the execution contract for the target repo.
- Use `templates/AGENTS.md.template`.
- Fill with repo-specific content: mission, language, build commands, authoritative files, forbidden actions, validation expectations.
- Do not leave generic placeholders. Every section must reflect the actual target repo.

---

### Step 6 — Create `docs/ai/REPO_MAP.md`

Create a human and agent-readable map of the repository.
- Use `templates/docs/ai/REPO_MAP.md.template`.
- Include: directory tree (top-level + key dirs), purpose of each major area, entry points, test locations, config files.
- Base it entirely on evidence from Step 2.

---

### Step 7 — Create `docs/ai/SOURCE_REFRESH.md`

Document how a future agent should re-sync its knowledge of this repo.
- Use `templates/docs/ai/SOURCE_REFRESH.md.template`.
- Include: key files to read first, how to rebuild/test, where state is recorded, how to detect staleness.

---

### Step 8 — Create `docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md`

Record vendor-specific AI knowledge relevant to this repo.
- Use `templates/docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template`.
- Include: relevant APIs, SDKs, frameworks, or platform constraints an agent would need to know.
- If the repo uses no AI-specific vendor tooling, record that explicitly.

---

### Step 9 — Create `IMPLEMENTATION_TRACKER.md`

Create the live state file for the target repo.
- Use `templates/IMPLEMENTATION_TRACKER.md.template`.
- Record: this bootstrap run as Milestone 1, files created, decisions made, validation status.
- Mark this run clearly: what is complete and what is recommended for future milestones.

---

### Step 10 — Validate

Run or simulate validation:
- Confirm all required files from `bootstrap-manifest.yaml` (`target_repo_required_files`) are present.
- Confirm no files still contain unfilled `{{PLACEHOLDER}}` markers.
- Confirm `artifacts/ai/repo_discovery.json` is valid JSON.
- Record the validation result in `IMPLEMENTATION_TRACKER.md`.

---

### Step 11 — Output summary

Provide a concise summary:
1. Files created and updated (with paths)
2. Key decisions made (with rationale)
3. Validation results
4. Unresolved gaps or unknowns
5. Recommended next milestone

---

## Stop conditions

Stop this run if:
- You are about to invent content not supported by evidence. Record the gap instead.
- You are asked to implement features or refactor code. That is out of scope for bootstrap.
- You have completed all required files and the tracker is up to date.
- You find an existing complete bootstrap in the target repo. Treat it as a resume-work scenario instead.

---

## Forbidden actions during this run

- Do not modify application code.
- Do not implement features.
- Do not refactor existing code.
- Do not add dependencies.
- Do not perform more than one bounded scope per session.
- Do not mark bootstrap complete without running validation.
