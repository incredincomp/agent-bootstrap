# Bootstrap Versioning and Upgrade Policy

This document defines the versioning model and compatibility/upgrade policy
for the agent-bootstrap system.

---

## Version source of truth

The bootstrap version is defined in the `VERSION` file at the root of this
repository. It contains a single semantic version string (e.g., `0.13.0`).

This file is:
- Human-readable and easy to update manually.
- Read by `apply_bootstrap.py` and `refresh_bootstrap.py` at run time.
- Checked by `validate_bootstrap.py` as a required file.
- Not dependent on git being present (safe for offline and CI contexts).

The git commit SHA is recorded separately as `Bootstrap source revision` in
the target repo marker, as supplemental traceability metadata.

---

## Version recorded in target repos

When `apply_bootstrap.py` runs against a target repo, it writes two fields
into `bootstrap/BOOTSTRAP_SOURCE.md`:

| Field | Value | Example |
|-------|-------|---------|
| Bootstrap source version | semver from `VERSION` file | `0.13.0` |
| Bootstrap source revision | git SHA of the bootstrap repo | `abc1234` |

These fields allow a target repo's maintainer to answer:
- What bootstrap version was this repo bootstrapped from?
- Exactly which commit of the bootstrap source was used?

---

## Semver semantics for bootstrap releases

The bootstrap system uses [Semantic Versioning](https://semver.org/):
`MAJOR.MINOR.PATCH`

### Patch release (e.g., `0.13.0` → `0.13.1`)
Fixes and clarifications that are safe to refresh without manual review:
- Documentation and wording corrections in templates.
- Script bug fixes that do not change marker structure or behavior.
- Cosmetic changes to prompts.

**Refresh safety**: Safe. `refresh_bootstrap.py` will classify most files as
`unchanged` or `safe-refresh`. No manual review expected.

### Minor release (e.g., `0.13.0` → `0.14.0`)
Additive capability changes:
- New template files added to the scaffold.
- New profiles added.
- New optional fields added to the marker.
- Script enhancements that are backward-compatible.

**Refresh safety**: Bounded review recommended. New files will be created
as `missing`. Existing files are refreshed only if still unpopulated.
Populated repo-specific files are skipped unless `--force` is used.

### Major release (e.g., `0.13.0` → `1.0.0`)
Structural or policy-breaking changes:
- Marker field renames or removals.
- Required file renames or restructuring.
- Breaking changes to apply/refresh/validate behavior.
- Policy changes that require manual intervention in target repos.

**Refresh safety**: Manual review required. `refresh_bootstrap.py` will emit
a warning when major-version drift is detected. Do not use `--force` without
inspecting the target repo's state first. Consider running `--dry-run` to
review the planned changes.

---

## Refresh safety rules

| Scenario | Expected behavior |
|----------|-------------------|
| Same major, patch/minor drift | Safe to run `refresh_bootstrap.py` |
| Major version drift | Run with `--dry-run` first; review before applying |
| Target has no version in marker (pre-0.13.0) | Treated as pre-versioning; proceed with caution |
| Target marker still has unfilled placeholders | `safe-refresh` classification; auto-updated |
| Target marker is fully populated | `populated` classification; skipped unless `--force` |

---

## How to bump the bootstrap version

1. Decide whether the change is a patch, minor, or major release.
2. Update the `VERSION` file with the new version string.
3. Add an entry to `CHANGELOG.md` under `[Unreleased]`, then rename that
   section to `[X.Y.Z] — YYYY-MM-DD`.
4. Commit and tag the release: `git tag vX.Y.Z`.
5. Update `IMPLEMENTATION_TRACKER.md` with the release decision.

No automated release pipeline is required. Tagging is a human decision.

---

## Treating pre-version markers

Target repos bootstrapped before `0.13.0` will have a git SHA (or empty value)
in `Bootstrap source version`. The `refresh_bootstrap.py` script treats these
as pre-versioning markers:
- No major-version drift warning is emitted (cannot compare).
- The marker is refreshed normally if classified as `safe-refresh`.
- The new version field is written on the next refresh or re-apply.

Maintainers of pre-version repos can run:
```
python scripts/refresh_bootstrap.py --target-dir /path/to/repo
```
This will update the marker with the current semver version on the next refresh.

---

## Profile-related version considerations

Profile template changes follow the same patch/minor/major rules above, scoped
to the affected profile:
- A new profile template file → minor release.
- Corrections to existing profile template content → patch release.
- Removing or renaming a profile → major release.

Profile selection is still explicit. Version bumps do not auto-migrate target
repos to a different profile.

---

## Apply vs refresh: version information flow

```
apply_bootstrap.py
  Reads: VERSION file → bootstrap_version
         git HEAD SHA  → bootstrap_revision
  Writes to marker: Bootstrap source version = bootstrap_version
                    Bootstrap source revision = bootstrap_revision

refresh_bootstrap.py
  Reads: VERSION file → current_version
         git HEAD SHA  → current_revision
         target marker → prior_version (for comparison)
  Reports: prior version vs current version
  Warns:   if major versions differ
  Writes:  updated marker with current_version and current_revision
```
