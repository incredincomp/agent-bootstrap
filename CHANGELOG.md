# Changelog

All notable changes to the agent-bootstrap system are recorded here.

Formal versioning begins with this release (Milestone 13). Earlier milestones
(1–12) are recorded below as pre-release development history for context.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.13.0] — 2026-03-14

First formalized bootstrap release. Establishes the versioning and upgrade
policy for the bootstrap system.

### Added
- `VERSION` file as the single source of truth for the bootstrap version.
- `CHANGELOG.md` (this file) for recording changes across releases.
- `docs/BOOTSTRAP_VERSIONING.md` with the compatibility and upgrade policy:
  semver semantics, patch/minor/major definitions, refresh-safety expectations,
  and guidance for pre-version markers.
- `Bootstrap source revision` row in `templates/bootstrap/BOOTSTRAP_SOURCE.md.template`
  to record the git commit SHA separately from the semver version.
- `BOOTSTRAP_SOURCE_REVISION` auto-filled placeholder in apply and refresh scripts.
- Version comparison output in `refresh_bootstrap.py` (current vs prior version).
- Major-version drift warning in `refresh_bootstrap.py` when the target's
  recorded version has a different major than the current bootstrap version.
- Version readability check in `validate_bootstrap.py` for the `VERSION` file.

### Changed
- `BOOTSTRAP_SOURCE_VERSION` in the bootstrap marker now records the semver
  version from the `VERSION` file rather than a raw git SHA. The git SHA is
  now recorded separately as `BOOTSTRAP_SOURCE_REVISION`.
- `apply_bootstrap.py` and `refresh_bootstrap.py` read `VERSION` for the
  primary version and use git SHA only as supplemental revision metadata.
- `validate_bootstrap.py` requires `VERSION`, `CHANGELOG.md`, and
  `docs/BOOTSTRAP_VERSIONING.md` as part of the bootstrap source repo.
- `bootstrap-manifest.yaml` updated to reference new required files and
  `BOOTSTRAP_SOURCE_REVISION` as an auto-filled placeholder.

### Policy
- See `docs/BOOTSTRAP_VERSIONING.md` for the full upgrade and compatibility policy.

---

## Pre-release development history (Milestones 1–12)

The following milestones were completed before formal versioning was established.
No release tags correspond to these entries; they are recorded for context only.

- **Milestone 12** — Manifest-driven bootstrap profiles (generic, python-service,
  infra-repo, vscode-extension, kubernetes-platform).
- **Milestone 11** — Safe refresh / upgrade lifecycle path (`refresh_bootstrap.py`).
- **Milestone 10** — GitHub Actions CI regression gate.
- **Milestone 9** — End-to-end fixture self-test harness.
- **Milestone 8** — Target-repo scaffold apply path (`apply_bootstrap.py`).
- **Milestone 7** — Target-repo validation mode in `validate_bootstrap.py`.
- **Milestone 6** — Schemas for `repo_discovery.json` and `implementation_tracker`.
- **Milestone 5** — Prompts: `new-repo-bootstrap`, `existing-repo-discovery`,
  `resume-work`, `bounded-implementation`, `closeout-and-handoff`.
- **Milestone 4** — Templates: `AGENTS.md`, `IMPLEMENTATION_TRACKER.md`,
  `REPO_MAP.md`, `SOURCE_REFRESH.md`, `AI_AGENT_VENDOR_KNOWLEDGE_BASE.md`,
  `BOOTSTRAP_SOURCE.md`, `repo_discovery.json`.
- **Milestone 3** — `bootstrap-manifest.yaml` control plane established.
- **Milestones 1–2** — Initial repo structure, `AGENTS.md`, `IMPLEMENTATION_TRACKER.md`,
  `validate_bootstrap.py`.
