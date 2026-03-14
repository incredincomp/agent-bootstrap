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

## Bootstrap profiles

Profiles let you apply a slightly different scaffold shape depending on the target
repository type. They provide more relevant starting guidance without inventing repo-specific content.

### What profiles do and do not do

**Profiles do:**
- Select profile-specific template variants where they materially improve guidance
  (currently: `docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md` has per-profile variants)
- Record the selected profile in `bootstrap/BOOTSTRAP_SOURCE.md` for future reference
- Allow `refresh_bootstrap.py` to use the same profile-specific templates when upgrading

**Profiles do not:**
- Auto-populate repo-specific discovery content (that remains agent-led)
- Replace the bootstrap prompt / discovery step
- Infer which profile to use — you must select one explicitly

### Supported profiles

| Profile | Suitable for |
|---------|-------------|
| `generic` | Any repo not covered by a more specific profile (default) |
| `python-service` | Python service or library repositories |
| `infra-repo` | Infrastructure/platform repos (Terraform, Pulumi, Ansible, etc.) |
| `vscode-extension` | VS Code extension repositories |
| `kubernetes-platform` | Kubernetes operator or platform repositories |

### Apply with a profile

```bash
# Apply with the default (generic) profile:
python scripts/apply_bootstrap.py --target-dir /path/to/target-repo

# Apply with a specific profile:
python scripts/apply_bootstrap.py --target-dir /path/to/target-repo --profile python-service
python scripts/apply_bootstrap.py --target-dir /path/to/target-repo --profile infra-repo
python scripts/apply_bootstrap.py --target-dir /path/to/target-repo --profile vscode-extension
python scripts/apply_bootstrap.py --target-dir /path/to/target-repo --profile kubernetes-platform

# Preview what a profile apply would create:
python scripts/apply_bootstrap.py --target-dir /path/to/target-repo --profile python-service --dry-run
```

An unknown profile name causes apply to exit with an error and list the supported options.

### Common core vs profile-specific behavior

The **common core** (applied for all profiles) includes:
- `AGENTS.md` — execution contract template
- `IMPLEMENTATION_TRACKER.md` — live state template
- `docs/ai/REPO_MAP.md` — repository map template
- `docs/ai/SOURCE_REFRESH.md` — source refresh instructions
- `bootstrap/BOOTSTRAP_SOURCE.md` — bootstrap origin marker
- `artifacts/ai/repo_discovery.json` — discovery artifact template

The **profile-specific overlay** replaces:
- `docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md` — a profile-tuned variant with guidance
  comments specific to that repo family (Python packaging, IaC providers, VS Code APIs, etc.)

All other files use the same common template regardless of profile.

### How refresh interacts with profile metadata

`refresh_bootstrap.py` reads the `Bootstrap profile` field from
`bootstrap/BOOTSTRAP_SOURCE.md` and uses the same profile-specific templates when
upgrading managed files. If no profile is recorded (e.g., the repo was bootstrapped
before Milestone 12), refresh falls back to the `generic` profile automatically.

### Why profiles do not replace repo discovery

Profiles select which templates to stage — they do not fill those templates with
repo-specific content. After apply, the `{{PLACEHOLDER}}` markers in profile-specific
templates still require an agent to inspect the target repo and fill them with real
evidence, using the bootstrap or discovery prompt.

---

## Refreshing an already-bootstrapped target repo

`scripts/refresh_bootstrap.py` upgrades an already-bootstrapped target repository
to align with the current canonical bootstrap source templates.

**Refresh is safe by default.** It never blindly overwrites repo-specific populated
content. It classifies each managed file before taking action.

### When to use refresh vs apply

| Situation | Tool |
|-----------|------|
| Target repo has never been bootstrapped | `scripts/apply_bootstrap.py` |
| Target repo was bootstrapped before; templates have been updated | `scripts/refresh_bootstrap.py` |
| Checking status of a bootstrapped repo | `scripts/refresh_bootstrap.py --dry-run` |

### File classifications

| Classification | Meaning | Default action |
|----------------|---------|----------------|
| `missing` | File not present in target | Created |
| `unchanged` | File matches current template exactly | Skipped (already current) |
| `safe-refresh` | File differs from template but still has unfilled `{{PLACEHOLDER}}` markers | Refreshed (template updated; no local content to lose) |
| `populated` | File has been filled with real content (no remaining placeholders) | **Skipped** — flagged for manual review |

### Example commands

```bash
# Preview what would change (no files written):
python scripts/refresh_bootstrap.py --target-dir /path/to/target-repo --dry-run

# Run refresh (safe defaults — skips populated files):
python scripts/refresh_bootstrap.py --target-dir /path/to/target-repo

# Preview what --force would overwrite (including populated files):
python scripts/refresh_bootstrap.py --target-dir /path/to/target-repo --dry-run --force

# Refresh and overwrite even populated files (destructive — use with care):
python scripts/refresh_bootstrap.py --target-dir /path/to/target-repo --force
```

### What refresh does

1. Detects whether the target repo was previously bootstrapped (checks for `bootstrap/BOOTSTRAP_SOURCE.md`).
2. Reads the prior bootstrap version and date from the marker if present.
3. Classifies each managed file (`missing`, `unchanged`, `safe-refresh`, or `populated`).
4. Creates missing files and refreshes unpopulated scaffold files by default.
5. Skips files that have been populated with real content (no remaining `{{PLACEHOLDER}}` markers).
6. Prints a summary of all classifications and actions taken.

### What refresh does NOT do

- It does **not** blindly overwrite populated files (unless `--force` is given).
- It does **not** auto-merge repo-specific content with template changes.
- It does **not** replace the agent population step — manually review flagged files.

### Recommended workflow before and after refresh

```bash
# 1. Preview the impact (always start here):
python scripts/refresh_bootstrap.py --target-dir /path/to/target-repo --dry-run

# 2. Review which files would be skipped (populated) vs refreshed.
#    For populated files, manually compare them to the updated template.

# 3. Run the refresh:
python scripts/refresh_bootstrap.py --target-dir /path/to/target-repo

# 4. Re-populate any refreshed files that need updated content.

# 5. Validate the final state:
python scripts/validate_bootstrap.py --target-dir /path/to/target-repo
```

### Apply vs refresh vs validate — key distinction

| Step | Tool | What it does |
|------|------|--------------|
| **Apply** | `scripts/apply_bootstrap.py` | Stages canonical file structure into a fresh target repo |
| **Refresh** | `scripts/refresh_bootstrap.py` | Updates managed files in an existing bootstrapped repo (safe by default) |
| **Validate** | `scripts/validate_bootstrap.py` | Checks file presence, placeholder completion, and JSON validity |

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

## End-to-end fixtures and self-test harness

`fixtures/` contains controlled minimal target repositories and population data
used to prove the bootstrap apply and validate workflow end-to-end.

`scripts/run_fixture_selftest.py` orchestrates the proof flow against each fixture.

### Three fixture states

| State | Description | Validation result |
|-------|-------------|-------------------|
| **A** — raw fixture | Fixture as committed; no bootstrap files present | N/A (starting point) |
| **B** — scaffold applied | `apply_bootstrap.py` run; placeholders present | Expected to **fail** (unfilled placeholders) |
| **C** — minimally populated | Placeholder values applied from `fixtures/population/*.json` | Expected to **pass** |

State B failing is **correct behavior** — it proves the scaffold was staged but not yet
populated, exactly as documented. State C passing proves the full population path works.

**State C population data is fixture-only proof data.** It is not the result of real
discovery and does not replace evidence-driven agent work. It exists only to prove
that a fully populated bootstrap passes validation.

### Example commands

```bash
# Run all fixtures (State B + State C):
python scripts/run_fixture_selftest.py

# Run a specific fixture only:
python scripts/run_fixture_selftest.py --fixture minimal-python-service

# State B only (scaffold staging proof, skip population):
python scripts/run_fixture_selftest.py --state-b-only

# Verbose output + inspect working copies:
python scripts/run_fixture_selftest.py --verbose --keep-work-dir
```

### Expected output

```
Bootstrap self-test
  ...
  minimal-python-service                    B:PASS  C:PASS
  minimal-infra-repo                        B:PASS  C:PASS

SELF-TEST PASSED.
```

### Fixture descriptions

| Fixture | Shape | Why |
|---------|-------|-----|
| `minimal-python-service` | Code-oriented (Flask, pytest) | Proves bootstrap on a typical application repo |
| `minimal-infra-repo` | Infra/docs-oriented (Terraform) | Proves bootstrap on a non-application, docs-heavy repo |

See `fixtures/README.md` for full fixture documentation.

---



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
# Stage the bootstrap scaffold into a target repo (default generic profile):
python scripts/apply_bootstrap.py --target-dir /path/to/target-repo

# Stage with a profile (e.g., for a Python service repo):
python scripts/apply_bootstrap.py --target-dir /path/to/target-repo --profile python-service

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
│  │  └─ AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template   ← generic (default)
│  ├─ profiles/                       ← profile-specific template overrides
│  │  ├─ python-service/docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template
│  │  ├─ infra-repo/docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template
│  │  ├─ vscode-extension/docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template
│  │  └─ kubernetes-platform/docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template
│  └─ artifacts/ai/
│     └─ repo_discovery.json.template
├─ fixtures/                          ← fixture target repos + self-test data
│  ├─ README.md                       ← fixture documentation
│  ├─ targets/
│  │  ├─ minimal-python-service/      ← code-oriented fixture (Flask, pytest)
│  │  └─ minimal-infra-repo/          ← infra/docs-oriented fixture (Terraform)
│  └─ population/
│     ├─ minimal-python-service.json  ← State C proof data
│     └─ minimal-infra-repo.json      ← State C proof data
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
   ├─ apply_bootstrap.py              ← scaffold apply script
   └─ run_fixture_selftest.py         ← end-to-end self-test harness
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

## Continuous integration

A GitHub Actions workflow at `.github/workflows/ci.yml` runs automatically on every push,
pull request, and manual trigger.

### What it checks

| Step | Command |
|------|---------|
| Script syntax | `python -m py_compile scripts/*.py` |
| Bootstrap repo structure | `python scripts/validate_bootstrap.py` |
| Fixture end-to-end self-tests | `python scripts/run_fixture_selftest.py` |

### When it runs

- Every push to any branch
- Every pull request
- On demand via the GitHub Actions "Run workflow" button

### Relationship to local validation

CI runs the same commands you should run locally before pushing:

```bash
python scripts/validate_bootstrap.py
python scripts/run_fixture_selftest.py
```

If CI fails, the failure maps directly to one of these commands — inspect the step
that failed to identify which check broke.

### What regressions it catches

- Missing required bootstrap repo files
- Broken or invalid JSON schemas and templates
- `apply_bootstrap.py` failures (scaffold apply path)
- `validate_bootstrap.py` failures (validation path)
- Fixture self-test failures (State B, State C, or State D refresh)
- Python syntax errors in any of the three scripts

> **Note for maintainers:** After merging changes that update the CI workflow or add new
> scripts, confirm that GitHub Actions is actually firing on subsequent pushes and pull
> requests by checking the Actions tab in the repository. The workflow was added in
> Milestone 10 and should run automatically for all branches.

---

## Bootstrap status and release workflow

### Checking bootstrap repo status

```bash
python scripts/bootstrap_status.py
```

Reports: version, git revision, CHANGELOG presence, core docs and scripts,
supported profiles, and version/changelog coherence.

### Inspecting a target repo marker

```bash
python scripts/bootstrap_status.py --target-dir /path/to/target-repo
```

Reports: bootstrap source, version, revision, date, agent, prompt, profile,
and era classification (pre-version, pre-profile, or versioned).

### Version/changelog coherence check

The coherence check (run automatically by `validate_bootstrap.py` and
`bootstrap_status.py`) confirms:
- `VERSION` exists and contains a valid semver string.
- `CHANGELOG.md` exists.
- The current version appears in `CHANGELOG.md` as a release heading, OR
  an `[Unreleased]` section is present (version in progress).

```bash
python scripts/validate_bootstrap.py  # includes coherence check
python scripts/bootstrap_status.py    # human-readable summary
```

### Release workflow

See [`docs/BOOTSTRAP_RELEASE_WORKFLOW.md`](docs/BOOTSTRAP_RELEASE_WORKFLOW.md)
for the full step-by-step release checklist, including:
- When to use patch/minor/major bumps.
- What files to update.
- What local checks to run before merge.
- How to tag a release.

---

## Bootstrap versioning

### Version source of truth

The bootstrap version is defined in the `VERSION` file at the root of this repository.
It contains a single semantic version string (e.g., `0.13.0`).

```bash
cat VERSION
# 0.13.0
```

`apply_bootstrap.py` and `refresh_bootstrap.py` read this file at run time to record
the bootstrap version in the target repo's marker.

### What the marker records

When `apply_bootstrap.py` runs, it writes two version fields into `bootstrap/BOOTSTRAP_SOURCE.md`:

| Field | Value | Example |
|-------|-------|---------|
| Bootstrap source version | semver from `VERSION` file | `0.13.0` |
| Bootstrap source revision | git SHA of the bootstrap repo | `abc1234` |

The `refresh_bootstrap.py` script reads the prior version from the marker, shows it
alongside the current version, and emits a warning if the major version has changed.

### Patch / minor / major semantics

| Change type | Example | Refresh safety |
|-------------|---------|---------------|
| Patch | Doc corrections, script bug fixes | Safe — no manual review expected |
| Minor | New templates, new profiles, additive marker fields | Bounded review — new files created; existing populated files skipped |
| Major | Marker field renames, structural policy changes | Manual review required — run `--dry-run` first |

### How to bump the version

1. Update the `VERSION` file.
2. Add an entry to `CHANGELOG.md`.
3. Commit and tag: `git tag vX.Y.Z`.

Full policy details are in [`docs/BOOTSTRAP_VERSIONING.md`](docs/BOOTSTRAP_VERSIONING.md).

---

## Limitations and non-goals

- This repo does **not** implement a CLI for end-users.
- This repo does **not** contain target-repo-specific content.
- This repo does **not** automate deployments or CI pipelines.
- Templates contain **placeholders**, not real project data.
- The validation script checks **file presence**, not semantic correctness.
- Schemas enforce **shape**, not business logic.
