# Prompt: Bounded Implementation

**Purpose:** Execute one bounded implementation milestone in a repository that has already been bootstrapped and has a declared next milestone.

**When to use:** The target repo has `AGENTS.md`, `IMPLEMENTATION_TRACKER.md`, and a clearly stated "Next milestone." You are executing exactly that milestone — nothing more.

**Scope:** One milestone only. Read the tracker. Declare the scope. Execute. Validate. Update the tracker. Stop.

---

## Instructions

You are executing one bounded implementation milestone. Follow these steps in order. Do not skip validation. Do not expand scope without recording the decision.

---

### Step 1 — Read the execution contract and tracker

Open and read:
1. `AGENTS.md` — know the forbidden actions and validation expectations.
2. `IMPLEMENTATION_TRACKER.md` — know the next declared milestone and its acceptance criteria.

If either file is missing, stop and use `prompts/resume-work.md` or `prompts/new-repo-bootstrap.md` instead.

---

### Step 2 — Declare the milestone

State explicitly:
- **Milestone name:** (from the tracker)
- **Scope:** The specific files, functions, or behaviors to create or modify.
- **Out of scope:** What you will not touch even if tempting.
- **Acceptance criteria:** How you will know the milestone is complete.
- **Validation plan:** What you will check before declaring done.

Post this declaration before writing a single line of code or creating any file.

---

### Step 3 — Inspect the relevant area

Before making any change, inspect the specific code or files in the milestone scope:
- Read the files you plan to modify.
- Understand the existing patterns, style, and conventions.
- Identify any dependencies or callers that will be affected.
- Note any risks or edge cases.

Do not rely on prior session memory. Use the current state of the files.

---

### Step 4 — Execute the milestone

Implement the declared changes:
- Match existing code style and conventions.
- Write tests for new behavior if tests exist in this repo.
- Keep changes logically coherent — one concern per change where possible.
- Do not silently fix unrelated issues. If you spot something, record it as a future item in the tracker.
- If you must deviate from the declared scope, stop and record the decision explicitly before deviating.

---

### Step 5 — Validate

After implementing:
- Run existing tests relevant to the changed area (record the command and result).
- Run the linter or formatter if one is configured (record the command and result).
- Confirm no unrelated tests were broken.
- Confirm new behavior matches the acceptance criteria declared in Step 2.
- If validation fails, fix it before proceeding. Do not skip validation.

---

### Step 6 — Update documentation

If your changes affect:
- `docs/ai/REPO_MAP.md` — update it.
- `docs/ai/SOURCE_REFRESH.md` — update if build/test commands changed.
- `AGENTS.md` — update if new authoritative files or forbidden actions apply.
- Any public-facing README or API docs — update if behavior changed.

Do not add documentation for speculative future behavior.

---

### Step 7 — Update the tracker

Record in `IMPLEMENTATION_TRACKER.md`:
- Milestone completed (with date).
- Files created or modified.
- Decisions made (with rationale).
- Validation results (commands run, pass/fail).
- Any follow-up items or open gaps.
- Updated "Next strongest bounded milestone."

---

### Step 8 — Output summary

Provide a concise summary:
1. Milestone executed
2. Files created or modified
3. Tests run and results
4. Decisions made
5. Follow-up items for the next milestone

---

## Stop conditions

Stop this run if:
- The declared milestone is complete and the tracker is updated.
- You discover the scope is significantly larger than declared. Stop, record the discovery, and recommend splitting the milestone.
- Tests are failing and you cannot fix them within the declared scope. Record the failure and stop.
- You are about to take an action forbidden by `AGENTS.md`. Stop and record the conflict.

---

## Scope expansion rules

Scope may be expanded in this session only if:
1. The expansion is directly required to complete the declared milestone (not just convenient).
2. The expansion is recorded as a decision in the tracker before being executed.
3. The expansion does not violate any forbidden actions in `AGENTS.md`.

Scope may **not** be expanded:
- To fix unrelated issues "while you're here."
- To add features not in the milestone.
- To refactor code outside the milestone scope.

---

## Forbidden actions during this run

- Do not start implementation before declaring the milestone scope.
- Do not skip reading `AGENTS.md` and `IMPLEMENTATION_TRACKER.md`.
- Do not implement features outside the declared scope without recording the decision.
- Do not skip tests or validation.
- Do not leave the tracker in a partial state.
- Do not modify files outside the declared scope without explicit justification.
