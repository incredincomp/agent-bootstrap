# Prompt: Existing Repository Discovery

**Purpose:** Perform thorough, evidence-based discovery on an existing repository before any changes are made. Produce a discovery artifact that future agents and humans can rely on.

**When to use:** The target repo has existing code and structure, and you need to understand it before creating operating files, planning a milestone, or resuming prior work.

**Scope:** Read-only analysis and documentation creation. Do not modify application code during this run.

---

## Instructions

You are performing discovery on an existing repository. Follow each step in order. Record everything you find.

---

### Step 1 — Establish discovery scope

Before starting, confirm:
- What is the target repository path or URL?
- Is there an existing `IMPLEMENTATION_TRACKER.md` or `AGENTS.md`? If yes, read them first — they may contain prior discoveries.
- Is there an existing `artifacts/ai/repo_discovery.json`? If yes, compare your findings against it to identify staleness.

---

### Step 2 — Top-level structure survey

List and categorize:
- All top-level files and directories
- Purpose of each (inferred from names, README, and brief content inspection)
- Which directories contain application code vs configuration vs documentation vs tests

Do not invent categories. Use only what you can observe.

---

### Step 3 — Language and technology stack

Identify:
- Primary programming language(s) (evidence: file extensions, lock files)
- Build system (evidence: Makefile, build.gradle, pyproject.toml, package.json, etc.)
- Package manager(s) and dependency files
- Runtime version constraints (evidence: .nvmrc, .python-version, go.mod, etc.)
- Test framework (evidence: test directory names, config files, CI steps)

---

### Step 4 — Entry points and key files

Identify:
- Main entry point(s) for the application
- Primary configuration files
- Environment variable definitions or .env.example files
- CI/CD configuration (GitHub Actions, Jenkinsfile, etc.)
- Infrastructure-as-code files (Terraform, Kubernetes manifests, Helm charts, etc.)
- Authentication or secrets management approach (note presence, not contents)

---

### Step 5 — Documentation survey

Identify:
- README quality (present, substantial, or stub?)
- Existing docs/ directory and its structure
- Any architecture decision records (ADRs) or design docs
- Existing agent-operating files (AGENTS.md, IMPLEMENTATION_TRACKER.md, docs/ai/)
- Any inline documentation standards (docstrings, JSDoc, etc.)

---

### Step 6 — Dependency and integration survey

Identify:
- External services or APIs this repo depends on (evidence: config files, import statements, README)
- Database(s) in use
- Message queues or event buses
- Third-party libraries of significance (evidence: dependency files)
- Upstream or downstream repo dependencies (if detectable)

---

### Step 7 — Risk and complexity notes

Note:
- Any areas of unusual complexity (evidence: file size, nesting depth, cyclomatic indicators)
- Any files or directories that appear stale or deprecated (evidence: comments, naming, git status if available)
- Any security-sensitive areas to approach carefully (evidence: auth code, secrets management, network calls)
- Any known gaps or TODOs (evidence: TODO comments, open issues if accessible)

---

### Step 8 — Record findings in `artifacts/ai/repo_discovery.json`

Create or update the discovery artifact:
- Use `templates/artifacts/ai/repo_discovery.json.template` if creating from scratch.
- Fill every field with evidence-based values.
- Use `null` for genuinely unknown fields; add a note in `discovery_notes`.
- Validate the JSON structure.
- Do not include contents of sensitive files (credentials, tokens, private keys).

---

### Step 9 — Update or create `docs/ai/REPO_MAP.md`

Create or update the repo map:
- Use `templates/docs/ai/REPO_MAP.md.template` if creating from scratch.
- If updating, compare current findings to the existing map and note changes.
- Include: directory tree, purpose of each major area, key files, entry points.

---

### Step 10 — Record findings in `IMPLEMENTATION_TRACKER.md`

Create or update the tracker:
- If no tracker exists, create one from `templates/IMPLEMENTATION_TRACKER.md.template`.
- Record this discovery run as a milestone.
- Note what was found, what was missing, what was surprising.
- List recommended next milestones based on findings.

---

### Step 11 — Output summary

Provide a concise summary:
1. Repository type and technology stack
2. Key findings (structure, entry points, documentation state)
3. Risk areas or gaps identified
4. Files created or updated
5. Recommended next milestone

---

## Stop conditions

Stop this run if:
- You are about to modify application code. That is out of scope.
- You are being asked to implement a feature during discovery. Record it as a future milestone instead.
- You have completed the discovery artifact and repo map and the tracker is up to date.

---

## Forbidden actions during this run

- Do not modify application code.
- Do not add dependencies.
- Do not refactor or "improve" existing code.
- Do not record contents of sensitive files.
- Do not invent findings not supported by evidence.
- Do not skip the output summary.
