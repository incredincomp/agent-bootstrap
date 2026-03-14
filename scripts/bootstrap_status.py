#!/usr/bin/env python3
"""
bootstrap_status.py

Reports the status of the agent-bootstrap source repository, or inspects a
bootstrapped target repository's bootstrap marker.

Usage:
    python scripts/bootstrap_status.py
    python scripts/bootstrap_status.py --repo-dir /path/to/bootstrap-repo
    python scripts/bootstrap_status.py --target-dir /path/to/target-repo

Exit codes:
    0 — status reported successfully
    1 — could not determine status (critical missing files or parse error)
"""

import argparse
import os
import re
import subprocess
import sys

# Shared bootstrap semantics
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPTS_DIR)
from bootstrap_core import (  # noqa: E402
    SEMVER_RE,
    read_version as _core_read_version,
    parse_bootstrap_marker,
    is_placeholder,
    classify_marker_era,
)

# ─────────────────────────────────────────────────────────────────────────────
# Core scripts expected in the bootstrap source repo
# ─────────────────────────────────────────────────────────────────────────────
CORE_SCRIPTS = [
    "scripts/validate_bootstrap.py",
    "scripts/apply_bootstrap.py",
    "scripts/refresh_bootstrap.py",
    "scripts/run_fixture_selftest.py",
    "scripts/bootstrap_status.py",
    "scripts/suggest_profile.py",
    "scripts/bootstrap_doctor.py",
]

CORE_DOCS = [
    "docs/BOOTSTRAP_VERSIONING.md",
    "docs/BOOTSTRAP_RELEASE_WORKFLOW.md",
]

# Markdown heading that introduces the changelog entry for a specific version,
# e.g. "## [0.13.0]" or "## [0.14.0] — 2026-01-01"
CHANGELOG_VERSION_RE = re.compile(r"^##\s+\[(\d+\.\d+\.\d+)\]")
CHANGELOG_UNRELEASED_RE = re.compile(r"^##\s+\[Unreleased\]", re.IGNORECASE)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def find_repo_dir(script_path):
    """Derive the repo root from the script location (scripts/ -> parent dir)."""
    scripts_dir = os.path.dirname(os.path.abspath(script_path))
    return os.path.dirname(scripts_dir)


def read_version(repo_dir):
    """Read VERSION file. Returns (version_string, error_message)."""
    return _core_read_version(repo_dir)


def read_git_revision(repo_dir):
    """Return the short git HEAD SHA, or None if git is unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def read_profiles_from_manifest(repo_dir):
    """Extract profile names from bootstrap-manifest.yaml (simple line scan)."""
    manifest_path = os.path.join(repo_dir, "bootstrap-manifest.yaml")
    if not os.path.isfile(manifest_path):
        return None
    profiles = []
    in_profiles = False
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("profiles:"):
                    in_profiles = True
                    continue
                if in_profiles:
                    # A top-level key (no leading space after the profiles: block)
                    # signals we have left the profiles section.
                    if stripped and not line.startswith(" ") and not line.startswith("\t"):
                        break
                    m = re.match(r"^\s{2}(\w[\w-]*):", line)
                    if m:
                        profiles.append(m.group(1))
    except OSError:
        return None
    return profiles if profiles else None


def check_changelog_coherence(repo_dir, version):
    """
    Check CHANGELOG.md for version coherence.

    Returns a list of issue strings (empty list = coherent).
    """
    issues = []
    changelog_path = os.path.join(repo_dir, "CHANGELOG.md")
    if not os.path.isfile(changelog_path):
        issues.append("CHANGELOG.md not found")
        return issues

    if version is None:
        issues.append("cannot check CHANGELOG coherence: VERSION unreadable")
        return issues

    has_unreleased = False
    found_versions = []
    try:
        with open(changelog_path, "r", encoding="utf-8") as f:
            for line in f:
                if CHANGELOG_UNRELEASED_RE.match(line):
                    has_unreleased = True
                m = CHANGELOG_VERSION_RE.match(line)
                if m:
                    found_versions.append(m.group(1))
    except OSError as exc:
        issues.append(f"cannot read CHANGELOG.md: {exc}")
        return issues

    if not has_unreleased and not found_versions:
        issues.append("CHANGELOG.md has no [Unreleased] section and no version entries")
    elif version not in found_versions and not has_unreleased:
        issues.append(
            f"current version {version} not in CHANGELOG.md and no [Unreleased] section"
        )

    return issues


# ─────────────────────────────────────────────────────────────────────────────
# Source repo status
# ─────────────────────────────────────────────────────────────────────────────

def report_source_status(repo_dir):
    """Print a human-readable status report for the bootstrap source repo."""
    print(f"Bootstrap source repository: {repo_dir}")
    print()

    # Version
    version, version_err = read_version(repo_dir)
    if version_err and version is None:
        print(f"  Version:        [MISSING] {version_err}")
    elif version_err:
        print(f"  Version:        {version}  [WARN] {version_err}")
    else:
        print(f"  Version:        {version}")

    # Git revision
    rev = read_git_revision(repo_dir)
    if rev:
        print(f"  Git revision:   {rev}")
    else:
        print(f"  Git revision:   (unavailable)")

    # CHANGELOG
    changelog_path = os.path.join(repo_dir, "CHANGELOG.md")
    if os.path.isfile(changelog_path):
        print(f"  CHANGELOG.md:   present")
    else:
        print(f"  CHANGELOG.md:   [MISSING]")

    # Core docs
    print()
    print("  Core docs:")
    for doc in CORE_DOCS:
        present = os.path.isfile(os.path.join(repo_dir, doc))
        status = "present" if present else "[MISSING]"
        print(f"    {doc}: {status}")

    # Core scripts
    print()
    print("  Core scripts:")
    for script in CORE_SCRIPTS:
        present = os.path.isfile(os.path.join(repo_dir, script))
        status = "present" if present else "[MISSING]"
        print(f"    {script}: {status}")

    # Profiles
    profiles = read_profiles_from_manifest(repo_dir)
    print()
    if profiles:
        print(f"  Profiles ({len(profiles)}): {', '.join(profiles)}")
    else:
        print("  Profiles:       (could not read from manifest)")

    # Coherence check
    print()
    print("  Version/changelog coherence:")
    issues = check_changelog_coherence(repo_dir, version)
    if issues:
        for issue in issues:
            print(f"    [WARN] {issue}")
    else:
        changelog_present = os.path.isfile(changelog_path)
        if version and changelog_present:
            print(f"    OK — version {version} is represented in CHANGELOG.md")
        else:
            print("    OK")

    print()


# ─────────────────────────────────────────────────────────────────────────────
# Target repo marker parsing and status
# ─────────────────────────────────────────────────────────────────────────────

def parse_marker(target_dir):
    """
    Parse bootstrap/BOOTSTRAP_SOURCE.md in a target repo.

    Returns a dict with the known marker fields (values may be None or the
    raw placeholder string if the field was never filled).
    """
    return parse_bootstrap_marker(target_dir)


def report_target_status(target_dir):
    """Print a human-readable status report for a bootstrapped target repo."""
    print(f"Bootstrapped target repository: {target_dir}")
    print()

    marker = parse_marker(target_dir)

    if not marker["found"]:
        print("  Bootstrap marker: [NOT FOUND] — bootstrap/BOOTSTRAP_SOURCE.md is missing")
        print()
        print("  This repo may not have been bootstrapped, or the marker was moved/deleted.")
        print()
        return

    print("  Bootstrap marker: present")
    print()

    def fmt(label, value):
        if value is None:
            return f"  {label:<30} (not recorded)"
        if is_placeholder(value):
            return f"  {label:<30} [UNFILLED] {value}"
        return f"  {label:<30} {value}"

    print(fmt("Source repository:", marker["source_repo"]))
    print(fmt("Bootstrap version:", marker["version"]))
    print(fmt("Bootstrap revision:", marker["revision"]))
    print(fmt("Bootstrap date:", marker["date"]))
    print(fmt("Agent / operator:", marker["agent"]))
    print(fmt("Prompt used:", marker["prompt"]))
    print(fmt("Bootstrap profile:", marker["profile"]))
    print()

    # Interpret marker era using shared classifier
    era = classify_marker_era(marker)
    version = marker["version"]
    if era == "pre-version":
        print("  Era:  pre-0.13.0 (no semver version recorded)")
    elif era == "versioned":
        major = int(version.split(".")[0])
        if major == 0:
            print(f"  Era:  versioned (pre-1.0 series, version {version})")
        else:
            print(f"  Era:  versioned (version {version})")
    else:
        print(f"  Era:  unknown (version field: {version!r})")

    profile = marker["profile"]
    if profile is None or is_placeholder(profile):
        print("  Profile: pre-profile or not recorded")
    else:
        print(f"  Profile: {profile}")

    print()


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Report the status of the bootstrap source repository, "
            "or inspect a bootstrapped target repository's bootstrap marker."
        )
    )
    parser.add_argument(
        "--repo-dir",
        default=None,
        help=(
            "Path to the bootstrap source repository root. "
            "Defaults to the parent of this script's directory."
        ),
    )
    parser.add_argument(
        "--target-dir",
        default=None,
        help="Path to a bootstrapped target repository to inspect.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.target_dir:
        target_dir = os.path.abspath(args.target_dir)
        report_target_status(target_dir)
        return

    repo_dir = args.repo_dir if args.repo_dir else find_repo_dir(sys.argv[0])
    repo_dir = os.path.abspath(repo_dir)
    report_source_status(repo_dir)


if __name__ == "__main__":
    main()
