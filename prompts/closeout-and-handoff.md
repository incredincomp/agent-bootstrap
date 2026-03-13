# Prompt: Closeout and Handoff

**Purpose:** Finalize a work session by completing validation, updating the tracker, writing handoff notes, and ensuring the repository is fully resumable by a future agent or human.

**When to use:** You have completed the declared milestone(s) for this session and need to formally close out before ending.

**Scope:** Validation + documentation + tracker finalization. No new feature work.

---

## Instructions

You are closing out a work session. Follow each step in order. Do not skip validation. Leave the repository in a state that any future agent can resume from with no chat history.

---

### Step 1 — Confirm milestone completion

For each milestone executed in this session:
- Verify the acceptance criteria declared at the start of the milestone were met.
- If any criterion was not met, record it as an open gap before proceeding.
- If you are closing out a bootstrap run, confirm all `target_repo_required_files` from `bootstrap-manifest.yaml` are present.

---

### Step 2 — Run full validation

Execute validation:
1. Run `scripts/validate_bootstrap.py` (or the equivalent for the target repo).
2. Run any existing tests in the repo: record the command and result.
3. Run the linter or formatter if configured: record the command and result.
4. Confirm no unfilled `{{PLACEHOLDER}}` markers remain in files created or modified this session.
5. Validate any JSON artifacts against their schemas.

Record every validation result — pass and fail — in the tracker. Do not skip failed validations; record them as open gaps instead.

---

### Step 3 — Cross-check internal references

Check:
- `README.md` layout section matches the actual file tree.
- `bootstrap-manifest.yaml` (or equivalent) required file list matches the actual files present.
- `AGENTS.md` authoritative file list is accurate.
- `docs/ai/REPO_MAP.md` reflects the current state of the repository.
- Any cross-references between files (e.g., "see X for details") actually point to existing content.

Record any discrepancies as open gaps.

---

### Step 4 — Write handoff notes

Create or update a "Handoff Notes" section in `IMPLEMENTATION_TRACKER.md`:

Include:
- **Session summary:** What was accomplished in this session in 2–3 sentences.
- **State at closeout:** Current phase, what is complete, what is not.
- **Open gaps:** Anything that was started but not finished, or discovered but not addressed.
- **Decisions made this session:** Key choices and their rationale.
- **Next milestone:** The single most important thing to do next, clearly scoped.
- **How to resume:** What files a future agent should read first, and in what order.

Write this for a reader with zero chat history.

---

### Step 5 — Update `docs/ai/SOURCE_REFRESH.md`

Confirm or update the source refresh instructions:
- Do they accurately describe how to rebuild understanding of this repo from scratch?
- Are the "key files to read first" current?
- Are the build/test commands current?
- Is the staleness detection guidance current?

---

### Step 6 — Final tracker update

Update `IMPLEMENTATION_TRACKER.md`:
- Mark all completed milestones as `✅ Complete`.
- Mark all open gaps as open items with clear descriptions.
- Confirm the "Next strongest bounded milestone" is specific and actionable.
- Record the closeout date.

The tracker must be complete enough that a future agent can read it and know exactly what to do next.

---

### Step 7 — Review for forbidden action violations

Self-review this session:
- Were any forbidden actions (from `AGENTS.md`) performed?
- Were any speculative changes made without recording decisions?
- Were any files modified outside the declared scope without justification?
- Were any tests skipped?

If yes to any of these: record the violation in the tracker and note remediation steps.

---

### Step 8 — Output summary

Provide the final session summary:

1. **Files created or updated** (with paths)
2. **Milestones completed** (with acceptance criteria outcomes)
3. **Validation results** (commands run, pass/fail)
4. **Decisions made** (with rationale)
5. **Open gaps** (with recommended remediation)
6. **Next recommended milestone** (scoped and actionable)

---

## Stop conditions

This closeout is complete when:
- All required files exist and contain repo-specific content.
- Validation has been run and results are recorded.
- The tracker is fully updated.
- Handoff notes are written for a zero-context future reader.
- The output summary has been provided.

---

## Forbidden actions during this run

- Do not implement new features or refactor code.
- Do not skip validation steps.
- Do not mark milestones complete without checking acceptance criteria.
- Do not write handoff notes that assume the reader has chat history.
- Do not leave `{{PLACEHOLDER}}` markers in files you created or modified.
- Do not omit open gaps from the tracker to make the closeout look cleaner.
