#!/usr/bin/env python3
"""
validate_bootstrap.py

Validates that the agent-bootstrap source repository contains all required files.
Can also validate a bootstrapped target repository for required files, unfilled
placeholders, and valid JSON artifacts.

Usage:
    python scripts/validate_bootstrap.py
    python scripts/validate_bootstrap.py --repo-dir /path/to/bootstrap-repo
    python scripts/validate_bootstrap.py --target-dir /path/to/target-repo
    python scripts/validate_bootstrap.py --verbose
    python scripts/validate_bootstrap.py --check-json

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
"""

import argparse
import json
import os
import re
import sys

# ─────────────────────────────────────────────────────────────────────────────
# Regex that matches unfilled template placeholders, e.g. {{REPO_NAME}}
# ─────────────────────────────────────────────────────────────────────────────
PLACEHOLDER_RE = re.compile(r"\{\{[A-Z_][A-Z0-9_]*\}\}")

# ─────────────────────────────────────────────────────────────────────────────
# Required files for the bootstrap SOURCE repository (this repo)
# ─────────────────────────────────────────────────────────────────────────────
BOOTSTRAP_REPO_REQUIRED_FILES = [
    "README.md",
    "AGENTS.md",
    "IMPLEMENTATION_TRACKER.md",
    "bootstrap-manifest.yaml",
    "prompts/new-repo-bootstrap.md",
    "prompts/existing-repo-discovery.md",
    "prompts/resume-work.md",
    "prompts/bounded-implementation.md",
    "prompts/closeout-and-handoff.md",
    "templates/AGENTS.md.template",
    "templates/IMPLEMENTATION_TRACKER.md.template",
    "templates/bootstrap/BOOTSTRAP_SOURCE.md.template",
    "templates/docs/ai/REPO_MAP.md.template",
    "templates/docs/ai/SOURCE_REFRESH.md.template",
    "templates/docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template",
    "templates/artifacts/ai/repo_discovery.json.template",
    "schemas/implementation_tracker.schema.json",
    "schemas/repo_discovery.schema.json",
    "scripts/validate_bootstrap.py",
    "scripts/apply_bootstrap.py",
    "scripts/run_fixture_selftest.py",
    "fixtures/targets/minimal-python-service/README.md",
    "fixtures/targets/minimal-python-service/conftest.py",
    "fixtures/targets/minimal-infra-repo/README.md",
    "fixtures/population/minimal-python-service.json",
    "fixtures/population/minimal-infra-repo.json",
    "fixtures/README.md",
]

# JSON files that must be parseable as valid JSON
JSON_FILES_TO_VALIDATE = [
    "schemas/implementation_tracker.schema.json",
    "schemas/repo_discovery.schema.json",
    "templates/artifacts/ai/repo_discovery.json.template",
]

# ─────────────────────────────────────────────────────────────────────────────
# Required files in a BOOTSTRAPPED TARGET repository
# ─────────────────────────────────────────────────────────────────────────────
TARGET_REPO_REQUIRED_FILES = [
    "AGENTS.md",
    "IMPLEMENTATION_TRACKER.md",
    "docs/ai/REPO_MAP.md",
    "docs/ai/SOURCE_REFRESH.md",
    "docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md",
    "bootstrap/BOOTSTRAP_SOURCE.md",
    "artifacts/ai/repo_discovery.json",
]

# Target-repo files that must have no unfilled {{PLACEHOLDER}} markers
TARGET_REPO_PLACEHOLDER_FILES = [
    "AGENTS.md",
    "IMPLEMENTATION_TRACKER.md",
    "docs/ai/REPO_MAP.md",
    "docs/ai/SOURCE_REFRESH.md",
    "docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md",
    "bootstrap/BOOTSTRAP_SOURCE.md",
]

# Target-repo JSON artifacts that must be valid JSON
TARGET_REPO_JSON_FILES = [
    "artifacts/ai/repo_discovery.json",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate the agent-bootstrap source repository structure."
    )
    parser.add_argument(
        "--repo-dir",
        default=None,
        help="Path to the bootstrap repo root. Defaults to the directory containing this script's parent.",
    )
    parser.add_argument(
        "--target-dir",
        default=None,
        help=(
            "Path to a bootstrapped target repository. "
            "Validates required files, unfilled placeholders, and JSON artifacts. "
            "When provided, --repo-dir is ignored."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each check result (not just failures).",
    )
    parser.add_argument(
        "--check-json",
        action="store_true",
        default=True,
        help="Validate JSON files are parseable (default: enabled).",
    )
    parser.add_argument(
        "--no-check-json",
        dest="check_json",
        action="store_false",
        help="Skip JSON validation.",
    )
    return parser.parse_args()


def find_repo_dir(script_path):
    """Derive the repo root from the script location (scripts/ -> parent dir)."""
    scripts_dir = os.path.dirname(os.path.abspath(script_path))
    return os.path.dirname(scripts_dir)


def check_required_files(repo_dir, file_list, verbose):
    """Check that all required files exist. Returns (pass_count, fail_count, failures)."""
    failures = []
    pass_count = 0

    for rel_path in file_list:
        full_path = os.path.join(repo_dir, rel_path)
        if os.path.isfile(full_path):
            pass_count += 1
            if verbose:
                print(f"  [PASS] {rel_path}")
        else:
            failures.append(rel_path)
            print(f"  [FAIL] Missing: {rel_path}")

    return pass_count, len(failures), failures


def check_json_files(repo_dir, verbose):
    """Check that JSON/JSON-template files are valid JSON. Returns (pass_count, fail_count, failures)."""
    failures = []
    pass_count = 0

    for rel_path in JSON_FILES_TO_VALIDATE:
        full_path = os.path.join(repo_dir, rel_path)
        if not os.path.isfile(full_path):
            # Missing files are caught by check_required_files; skip here
            continue
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                json.load(f)
            pass_count += 1
            if verbose:
                print(f"  [PASS] Valid JSON: {rel_path}")
        except json.JSONDecodeError as exc:
            failures.append((rel_path, str(exc)))
            print(f"  [FAIL] Invalid JSON in {rel_path}: {exc}")

    return pass_count, len(failures), failures


def check_json_file_list(repo_dir, file_list, verbose):
    """Check that a given list of JSON files are valid JSON. Returns (pass_count, fail_count, failures)."""
    failures = []
    pass_count = 0

    for rel_path in file_list:
        full_path = os.path.join(repo_dir, rel_path)
        if not os.path.isfile(full_path):
            continue
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                json.load(f)
            pass_count += 1
            if verbose:
                print(f"  [PASS] Valid JSON: {rel_path}")
        except json.JSONDecodeError as exc:
            failures.append((rel_path, str(exc)))
            print(f"  [FAIL] Invalid JSON in {rel_path}: {exc}")

    return pass_count, len(failures), failures


def check_placeholders(repo_dir, file_list, verbose):
    """Check that no files contain unfilled {{PLACEHOLDER}} markers.
    Returns (pass_count, fail_count, failures). Reads files line-by-line to
    avoid loading very large files entirely into memory."""
    failures = []
    pass_count = 0

    for rel_path in file_list:
        full_path = os.path.join(repo_dir, rel_path)
        if not os.path.isfile(full_path):
            # Missing files are caught by check_required_files; skip here
            continue
        found = []
        with open(full_path, "r", encoding="utf-8") as f:
            for line in f:
                found.extend(PLACEHOLDER_RE.findall(line))
        if found:
            unique = sorted(set(found))
            failures.append((rel_path, unique))
            print(f"  [FAIL] Unfilled placeholders in {rel_path}: {', '.join(unique)}")
        else:
            pass_count += 1
            if verbose:
                print(f"  [PASS] No unfilled placeholders: {rel_path}")

    return pass_count, len(failures), failures


def main():
    args = parse_args()

    # ── Target-repo validation mode ────────────────────────────────────────
    if args.target_dir:
        target_dir = os.path.abspath(args.target_dir)
        print(f"Validating bootstrapped target repository: {target_dir}")
        print()

        total_pass = 0
        total_fail = 0

        print("=== Required file check ===")
        p, f, _ = check_required_files(target_dir, TARGET_REPO_REQUIRED_FILES, args.verbose)
        total_pass += p
        total_fail += f
        if f == 0:
            print(f"  All {p} required files present.")
        else:
            print(f"  {p} passed, {f} missing.")
        print()

        print("=== Placeholder check ===")
        p, f, _ = check_placeholders(target_dir, TARGET_REPO_PLACEHOLDER_FILES, args.verbose)
        total_pass += p
        total_fail += f
        if f == 0:
            print(f"  All {p} checked files have no unfilled placeholders.")
        else:
            print(f"  {p} passed, {f} have unfilled placeholders.")
        print()

        if args.check_json:
            print("=== JSON validity check ===")
            p, f, _ = check_json_file_list(target_dir, TARGET_REPO_JSON_FILES, args.verbose)
            total_pass += p
            total_fail += f
            if f == 0:
                print(f"  All {p} JSON files are valid.")
            else:
                print(f"  {p} passed, {f} invalid.")
            print()

        print("=== Summary ===")
        print(f"  Passed: {total_pass}")
        print(f"  Failed: {total_fail}")

        if total_fail > 0:
            print()
            print("TARGET VALIDATION FAILED. Fix the issues above before declaring bootstrap complete.")
            sys.exit(1)
        else:
            print()
            print("TARGET VALIDATION PASSED. Bootstrapped target repository is complete.")
            sys.exit(0)

    # ── Bootstrap source repo validation mode ─────────────────────────────
    repo_dir = args.repo_dir if args.repo_dir else find_repo_dir(sys.argv[0])
    repo_dir = os.path.abspath(repo_dir)

    print(f"Validating bootstrap repository: {repo_dir}")
    print()

    total_pass = 0
    total_fail = 0

    # ── Check 1: Required files ────────────────────────────────────────────
    print("=== Required file check ===")
    p, f, _ = check_required_files(repo_dir, BOOTSTRAP_REPO_REQUIRED_FILES, args.verbose)
    total_pass += p
    total_fail += f
    if f == 0:
        print(f"  All {p} required files present.")
    else:
        print(f"  {p} passed, {f} missing.")
    print()

    # ── Check 2: JSON validity ─────────────────────────────────────────────
    if args.check_json:
        print("=== JSON validity check ===")
        p, f, _ = check_json_files(repo_dir, args.verbose)
        total_pass += p
        total_fail += f
        if f == 0:
            print(f"  All {p} JSON files are valid.")
        else:
            print(f"  {p} passed, {f} invalid.")
        print()

    # ── Summary ───────────────────────────────────────────────────────────
    print("=== Summary ===")
    print(f"  Passed: {total_pass}")
    print(f"  Failed: {total_fail}")

    if total_fail > 0:
        print()
        print("VALIDATION FAILED. Fix the issues above before declaring bootstrap complete.")
        sys.exit(1)
    else:
        print()
        print("VALIDATION PASSED. Bootstrap repository structure is intact.")
        sys.exit(0)


if __name__ == "__main__":
    main()
