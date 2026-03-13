# agent-bootstrap

A reusable, production-grade bootstrap repository for AI agents.  
Use this repo as a source of truth when initializing, documenting, and operating on target repositories.

---

## What this repository is

`agent-bootstrap` is a **canonical scaffold and control-plane repository** that an AI agent (or human) can point at any target repository to:

1. Perform structured discovery on the target repo.
2. Understand how projects should be structured and documented.
3. Create required operating files in the target repo.
4. Leave behind durable project state for future agent sessions.

It is not a library, CLI tool, or deployment pipeline.  
It is a **documentation and prompt system** — the operating model for AI-assisted project work.

---

## Why it exists

AI agent sessions are ephemeral. Without durable state, every new session re-discovers the same things, makes the same assumptions, and risks contradicting prior work.

This repository solves that by providing:

- Machine-readable manifests that describe what a bootstrapped repo looks like.
- Reusable prompt files that enforce inspection-before-change discipline.
- Templates for the operating files every agent-assisted repo should have.
- Schemas for validating structured artifacts.
- A validation script to confirm a bootstrap repo is intact.

---

## Applying bootstrap to a target repo

`scripts/apply_bootstrap.py` stages the canonical scaffold into a target repository.
This is the fastest way to get a target repo ready for the discovery/bootstrap prompt.

**Apply does not auto-populate repo-specific content.** It copies template files with
their `{{PLACEHOLDER}}` markers intact. A human or agent then inspects the target repo
and fills those placeholders with real, evidence-based content.

### Example commands

```bash
# Preview what would be created (no files written):
python scripts/apply_bootstrap.py --target-dir /path/to/target-repo --dry-run

# Apply the scaffold (skips files that already exist):
python scripts/apply_bootstrap.py --target-dir /path/to/target-repo

# Re-apply and overwrite existing files:
python scripts/apply_bootstrap.py --target-dir /path/to/target-repo --force

# Preview what --force would overwrite:
python scripts/apply_bootstrap.py --target-dir /path/to/target-repo --dry-run --force
```

### What apply does

1. Creates required directories (`docs/ai/`, `bootstrap/`, `artifacts/ai/`).
2. Copies each canonical template to its target destination.
3. Writes `bootstrap/BOOTSTRAP_SOURCE.md` with the bootstrap source URL, version, and date filled in.
4. Skips any file that already exists (safe by default).
5. Prints a summary: created / skipped / would overwrite / overwritten / errors.

### What apply does NOT do

- It does **not** inspect the target repo or infer repo-specific content.
- It does **not** fill `{{PLACEHOLDER}}` markers (except the bootstrap system markers in `BOOTSTRAP_SOURCE.md`).
- It does **not** run discovery or populate `artifacts/ai/repo_discovery.json` with real findings.

### After apply: run the bootstrap prompt

Once the scaffold is staged, point an agent at the target repo using one of the prompts:

```
prompts/new-repo-bootstrap.md         ← for new or empty repos
prompts/existing-repo-discovery.md    ← for repos with existing code
```

The agent will inspect the target repo and fill all remaining `{{PLACEHOLDER}}` markers
with evidence found in the repo.

### Validate the result

After the agent has populated the files:

```bash
python scripts/validate_bootstrap.py --target-dir /path/to/target-repo
```

This checks:
- All required files are present.
- No unfilled `{{PLACEHOLDER}}` markers remain.
- JSON artifacts are valid.

### Apply vs bootstrap prompt — key distinction

| Step | Tool | What it does |
|------|------|--------------|
| **Apply** | `scripts/apply_bootstrap.py` | Stages canonical file structure and skeletal templates |
| **Bootstrap prompt / discovery** | `prompts/*.md` → agent session | Inspects target repo; fills templates with real evidence |

These are two separate steps. Apply first, then run the prompt.

---

### Initializing a new target repo

1. Clone or reference this repository.
2. Open `prompts/new-repo-bootstrap.md` and paste it into your agent session, pointing the agent at your target repo.
3. The agent will inspect the target repo, create the required operating files, and record its work in `IMPLEMENTATION_TRACKER.md`.

### Resuming work in a target repo

1. Open `prompts/resume-work.md` and paste it into a new agent session.
2. The agent will read the existing tracker and operating files before taking any action.

### Running a bounded implementation milestone

1. After bootstrap is complete, use `prompts/bounded-implementation.md`.
2. The agent will scope itself to a single milestone and update the tracker on completion.

### Closing out a session

1. Use `prompts/closeout-and-handoff.md` to finalize state, validate files, and prepare handoff notes.

---

## How an agent should consume this repository

An agent that receives a prompt from this repo's `prompts/` directory should:

1. Read `bootstrap-manifest.yaml` to understand required outputs and stop conditions.
2. Inspect the target repo before making any changes.
3. Use the templates in `templates/` as starting points, filling them with real evidence from the target repo.
4. Validate its outputs against the schemas in `schemas/`.
5. Run `scripts/validate_bootstrap.py` (or equivalent checks) before declaring bootstrap complete.
6. Update `IMPLEMENTATION_TRACKER.md` in the target repo with a full record of the run.

---

## What files this system creates in a target repo

| File | Purpose |
|------|---------|
| `AGENTS.md` | Execution contract for AI agents working in that repo |
| `IMPLEMENTATION_TRACKER.md` | Live state file: milestones, decisions, gaps |
| `docs/ai/REPO_MAP.md` | Human + agent-readable map of the repository |
| `docs/ai/SOURCE_REFRESH.md` | Instructions for re-syncing agent knowledge |
| `docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md` | Vendor-specific AI knowledge relevant to the repo |
| `bootstrap/BOOTSTRAP_SOURCE.md` | Record of where the bootstrap originated |
| `artifacts/ai/repo_discovery.json` | Machine-readable discovery artifact |

---

## What "bootstrap complete" means for a target repo

A target repo is considered bootstrap-complete when:

- All required files listed in `bootstrap-manifest.yaml` are present.
- Each file is populated with repo-specific content (not generic placeholders).
- `IMPLEMENTATION_TRACKER.md` records the run that created them.
- The discovery artifact (`repo_discovery.json`) reflects actual findings.
- A human or agent can open the tracker and understand the project state without chat history.

---

## Intended operating model

```
Inspect → Document → Bound → Validate → Record
```

1. **Inspect**: Read the target repo before touching anything.
2. **Document**: Create or update operating files with real evidence.
3. **Bound**: Limit each session to a declared milestone scope.
4. **Validate**: Confirm file presence, internal references, and schema compliance.
5. **Record**: Update the tracker; leave the repo resumable.

---

## Quick-start

```bash
# Stage the bootstrap scaffold into a target repo:
python scripts/apply_bootstrap.py --target-dir /path/to/target-repo

# Then run the bootstrap prompt (new repo) or discovery prompt (existing repo)
# against the target repo to fill in the content.

# Validate after the agent has populated the files:
python scripts/validate_bootstrap.py --target-dir /path/to/target-repo
```

---

## Repository layout

```
.
├─ README.md                          ← this file
├─ AGENTS.md                          ← execution contract for this repo
├─ IMPLEMENTATION_TRACKER.md          ← live state for this repo
├─ bootstrap-manifest.yaml            ← machine-readable control plane
├─ prompts/                           ← reusable agent prompt files
│  ├─ new-repo-bootstrap.md
│  ├─ existing-repo-discovery.md
│  ├─ resume-work.md
│  ├─ bounded-implementation.md
│  └─ closeout-and-handoff.md
├─ templates/                         ← canonical templates for target repos
│  ├─ AGENTS.md.template
│  ├─ IMPLEMENTATION_TRACKER.md.template
│  ├─ bootstrap/
│  │  └─ BOOTSTRAP_SOURCE.md.template
│  ├─ docs/ai/
│  │  ├─ REPO_MAP.md.template
│  │  ├─ SOURCE_REFRESH.md.template
│  │  └─ AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template
│  └─ artifacts/ai/
│     └─ repo_discovery.json.template
├─ examples/                          ← per-repo-type discovery notes
│  ├─ python-service/
│  ├─ infra-repo/
│  ├─ vscode-extension/
│  └─ kubernetes-platform/
├─ schemas/                           ← JSON schemas for structured artifacts
│  ├─ implementation_tracker.schema.json
│  └─ repo_discovery.schema.json
└─ scripts/
   ├─ validate_bootstrap.py           ← lightweight validation script
   └─ apply_bootstrap.py              ← scaffold apply script
```

---

## Example workflow: initializing a target repo

```
1. Agent receives prompt from prompts/new-repo-bootstrap.md
2. Agent inspects target repo → records findings in repo_discovery.json
3. Agent creates AGENTS.md, IMPLEMENTATION_TRACKER.md, docs/ai/* from templates
4. Agent fills templates with real evidence (no guessing)
5. Agent runs validate_bootstrap.py against target repo
6. Agent updates IMPLEMENTATION_TRACKER.md with completion status
7. Session ends — repo is resumable by any future agent or human
```

---

## Limitations and non-goals

- This repo does **not** implement a CLI for end-users.
- This repo does **not** contain target-repo-specific content.
- This repo does **not** automate deployments or CI pipelines.
- Templates contain **placeholders**, not real project data.
- The validation script checks **file presence**, not semantic correctness.
- Schemas enforce **shape**, not business logic.
