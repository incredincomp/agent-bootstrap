# Prompt: Resume Work

**Purpose:** Resume work in a repository that already has AI agent operating files. Restore full context before taking any action.

**When to use:** A prior agent session has left behind `AGENTS.md`, `IMPLEMENTATION_TRACKER.md`, and/or `docs/ai/` files. You are starting a new session and need to pick up where the previous session left off.

**Scope:** Context restoration + execution of the next declared milestone. Do not invent new scope.

---

## Instructions

You are resuming work in a repository. Context restoration comes before any action. Follow these steps in order.

---

### Step 1 — Read the execution contract

Open and read `AGENTS.md` in the target repository.

Confirm:
- What is the repo mission?
- What is in scope and out of scope?
- What are the authoritative files?
- What are the forbidden actions?
- What are the validation expectations?

Do not proceed until you have read this file. If it does not exist, treat this as a new bootstrap scenario and use `prompts/new-repo-bootstrap.md` instead.

---

### Step 2 — Read the implementation tracker

Open and read `IMPLEMENTATION_TRACKER.md` in the target repository.

Identify:
- Current phase
- Last completed milestone
- Next recommended milestone
- Any open gaps or unresolved items
- Files created or modified in prior sessions
- Any recorded decisions relevant to your next steps

If the tracker is missing or empty, treat this as a new bootstrap scenario.

---

### Step 3 — Read the repo map

Open `docs/ai/REPO_MAP.md` if it exists.

Use it to rebuild your understanding of the repo structure without re-surveying the entire codebase. Note if it appears stale (e.g., references files that no longer exist or missing recent additions).

---

### Step 4 — Spot-check current state

Perform a lightweight current-state check:
- Confirm the files listed as "created" in the tracker actually exist.
- Check for any obvious changes since the last session (new files, deleted files, modified configs).
- If the discovery artifact exists (`artifacts/ai/repo_discovery.json`), verify it is not significantly out of date.

Record any discrepancies between the tracker and the current state.

---

### Step 5 — Declare the milestone for this session

Based on your review of the tracker, declare:
- The milestone you will execute in this session.
- The specific files you expect to create or modify.
- The acceptance criteria for this milestone.
- Any known risks or blockers.

**Do not begin work until the milestone is declared.**  
If the tracker's recommended next milestone is unclear or contradictory, stop and resolve the ambiguity before proceeding (record the resolution in the tracker).

---

### Step 6 — Execute the declared milestone

Execute the declared milestone. While working:
- Stay within the declared scope.
- If you discover that the scope needs to expand, stop and record the decision before expanding.
- Do not silently perform extra work.
- If you hit a blocker, record it and stop rather than working around it with a workaround that violates the execution contract.

---

### Step 7 — Update the tracker

After completing the milestone:
- Record the milestone as complete with a date.
- List all files created or modified.
- Record all decisions made with rationale.
- Record validation results.
- List any open gaps or follow-up items.
- Update "Next strongest bounded milestone."

---

### Step 8 — Validate

- Confirm all files created or modified in this session are present and correct.
- Run `scripts/validate_bootstrap.py` if structural files were added or removed.
- Confirm no unfilled `{{PLACEHOLDER}}` markers remain in files you touched.
- Record validation results in the tracker.

---

### Step 9 — Output summary

Provide a concise summary:
1. Prior state when session started
2. Milestone executed and outcome
3. Files created or modified
4. Decisions made
5. Validation results
6. Next recommended milestone

---

## Stop conditions

Stop this run if:
- The tracker declares the repo is in a state that conflicts with what you observe. Resolve the conflict before proceeding.
- You are about to take an action that contradicts `AGENTS.md`. Stop and record the conflict.
- The declared milestone is complete and the tracker is updated.
- You encounter a blocker that requires human decision-making. Record it and stop.

---

## Forbidden actions during this run

- Do not take any action before reading `AGENTS.md` and `IMPLEMENTATION_TRACKER.md`.
- Do not invent prior context from chat history or assumptions.
- Do not perform work outside the declared milestone scope without recording the decision.
- Do not leave the tracker in a partial state — update it completely before ending the session.
- Do not ignore discrepancies between the tracker and current state.
