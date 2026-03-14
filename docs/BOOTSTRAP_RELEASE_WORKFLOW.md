# Bootstrap Release Workflow

This document describes the repeatable process for cutting a new bootstrap
release. Follow it before bumping the version or merging release-oriented changes.

---

## When to bump the version

| Change type | Version bump |
|-------------|-------------|
| Documentation fixes, wording corrections, cosmetic template edits | `PATCH` |
| New template files, new profiles, new optional marker fields, script enhancements | `MINOR` |
| Marker field renames/removals, required-file restructuring, breaking apply/refresh changes | `MAJOR` |

If unsure, prefer `PATCH`. Record the reasoning in `IMPLEMENTATION_TRACKER.md`.

See `docs/BOOTSTRAP_VERSIONING.md` for the full semver policy and refresh-safety
expectations.

---

## Pre-release checklist

Before updating `VERSION` or merging, confirm all of the following:

### 1. Local validation passes

```bash
python scripts/validate_bootstrap.py
```

Expected: `VALIDATION PASSED. Bootstrap repository structure is intact.`

### 2. Fixture self-tests pass

```bash
python scripts/run_fixture_selftest.py
```

Expected: `B:PASS C:PASS D:PASS` for every fixture.

### 3. Script syntax is clean

```bash
python -m py_compile scripts/validate_bootstrap.py scripts/apply_bootstrap.py \
    scripts/run_fixture_selftest.py scripts/refresh_bootstrap.py \
    scripts/bootstrap_status.py
```

### 4. Bootstrap status is coherent

```bash
python scripts/bootstrap_status.py
```

Check: no `[MISSING]` or `[WARN]` items for core files. Version/changelog
coherence should show `OK`.

### 5. CI is green

The GitHub Actions CI workflow must pass on the branch before merge. It runs:
- `py_compile` syntax check on all scripts
- `validate_bootstrap.py`
- `run_fixture_selftest.py`

Do not merge a release-oriented change with a failing CI run.

---

## Cutting the release

### Step 1 — Decide the version bump

Determine whether this is a patch, minor, or major release using the table above.

### Step 2 — Update VERSION

Edit `VERSION` at the repository root:
```
0.14.0
```

One line, no trailing whitespace, no `v` prefix.

### Step 3 — Update CHANGELOG.md

Move the `[Unreleased]` section content into a new dated release entry:

```markdown
## [0.14.0] — YYYY-MM-DD

### Added
- ...

### Changed
- ...
```

Add a fresh empty `[Unreleased]` section at the top:

```markdown
## [Unreleased]

---
```

### Step 4 — Update IMPLEMENTATION_TRACKER.md

Add a Milestone entry recording:
- The version bump decision and rationale
- Files created or modified
- Validation results

### Step 5 — Run local checks (again)

```bash
python scripts/validate_bootstrap.py && python scripts/run_fixture_selftest.py
python scripts/bootstrap_status.py
```

Confirm all pass cleanly and the status report shows the new version.

### Step 6 — Commit

Commit all changed files together:

```
git add VERSION CHANGELOG.md IMPLEMENTATION_TRACKER.md [any other changed files]
git commit -m "Bump version to 0.14.0: <brief description of what changed>"
```

### Step 7 — Tag (optional but recommended)

```
git tag v0.14.0
git push origin v0.14.0
```

Tagging is a human decision. It is not automated. Tags create a stable reference
point for target repos that record `Bootstrap source revision`.

### Step 8 — Post-merge verification

After merging (or pushing to the main branch):

1. Confirm CI passes on `main`.
2. Run `python scripts/bootstrap_status.py` from a fresh checkout if in doubt.
3. Note the release in `IMPLEMENTATION_TRACKER.md` under the relevant milestone.

---

## Updating bootstrap-manifest.yaml

If you added new required files (templates, scripts, docs), add them to:
- `BOOTSTRAP_REPO_REQUIRED_FILES` in `scripts/validate_bootstrap.py`
- `bootstrap_repo_required_files` in `bootstrap-manifest.yaml`

Both lists must stay in sync. The CI regression gate will catch drift because
`validate_bootstrap.py` checks for every file in its list.

---

## Adding a new profile

New profiles require updates in four places:
1. `PROFILES` dict in `scripts/apply_bootstrap.py`
2. `PROFILES` dict in `scripts/refresh_bootstrap.py`
3. `profiles:` section in `bootstrap-manifest.yaml`
4. A matching template file in `templates/profiles/<profile-name>/`

A new profile is a **minor** version bump. After adding it, run the fixture
self-test and confirm CI passes.

---

## Coherence rules (summary)

- `VERSION` must contain a valid semver string.
- `CHANGELOG.md` must exist.
- The current version must appear in `CHANGELOG.md` (as a release entry), OR
  there must be an `[Unreleased]` section (indicating the version is in progress).
- If `bootstrap-manifest.yaml` references a version field, it must match `VERSION`.

Run `python scripts/bootstrap_status.py` to check these automatically.

---

## What NOT to do

- Do not bump `VERSION` without updating `CHANGELOG.md`.
- Do not update `CHANGELOG.md` without bumping `VERSION` (except for adding to
  `[Unreleased]`).
- Do not push release commits with failing CI.
- Do not rename or remove marker fields (`BOOTSTRAP_SOURCE_VERSION`,
  `BOOTSTRAP_SOURCE_REVISION`) without a major version bump.
- Do not add release automation or tag-pushing to CI unless explicitly decided.
