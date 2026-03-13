#!/usr/bin/env python3
"""
run_fixture_selftest.py

End-to-end self-test harness for the agent-bootstrap system.

Three fixture states are tested for each fixture target repo:

  State A — raw fixture     : fixture as committed; no bootstrap files present
  State B — scaffold applied: apply_bootstrap.py has run; placeholders remain (expected)
  State C — minimally populated: placeholder values filled from fixtures/population/*.json;
                                  validate_bootstrap.py should pass with zero failures

Applies the bootstrap scaffold to controlled fixture target repositories and validates
the result, providing repeatable proof that the apply and validate paths work correctly.

State B failing validation is the *expected* outcome — it proves the scaffold was staged
but not yet populated, exactly as documented. State C passing proves the full path works.

Usage:
    python scripts/run_fixture_selftest.py
    python scripts/run_fixture_selftest.py --fixture minimal-python-service
    python scripts/run_fixture_selftest.py --fixture minimal-infra-repo
    python scripts/run_fixture_selftest.py --state-b-only
    python scripts/run_fixture_selftest.py --verbose
    python scripts/run_fixture_selftest.py --work-dir /tmp/my-selftest-work
    python scripts/run_fixture_selftest.py --keep-work-dir

Exit codes:
    0 — all tested fixtures passed
    1 — one or more fixtures failed
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

# Regex matching unfilled template placeholders, e.g. {{REPO_NAME}}
PLACEHOLDER_RE = re.compile(r"\{\{[A-Z_][A-Z0-9_]*\}\}")

# Paths relative to the bootstrap repo root
FIXTURES_TARGETS_DIR = "fixtures/targets"
FIXTURES_POPULATION_DIR = "fixtures/population"

# Available fixture names
ALL_FIXTURES = [
    "minimal-python-service",
    "minimal-infra-repo",
]

# Files in a bootstrapped target repo that are checked for unfilled placeholders.
# This mirrors TARGET_REPO_PLACEHOLDER_FILES in scripts/validate_bootstrap.py.
# Keep both lists in sync when adding new template files.
TARGET_PLACEHOLDER_FILES = [
    "AGENTS.md",
    "IMPLEMENTATION_TRACKER.md",
    "docs/ai/REPO_MAP.md",
    "docs/ai/SOURCE_REFRESH.md",
    "docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md",
    "bootstrap/BOOTSTRAP_SOURCE.md",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run end-to-end bootstrap self-tests against fixture target repositories. "
            "Tests State B (scaffold applied, placeholders expected) and optionally "
            "State C (placeholders filled, validation should pass)."
        )
    )
    parser.add_argument(
        "--fixture",
        default=None,
        help="Name of a specific fixture to test. Defaults to all fixtures.",
    )
    parser.add_argument(
        "--state-b-only",
        action="store_true",
        help="Test State B only (scaffold applied). Skip State C population and validation.",
    )
    parser.add_argument(
        "--work-dir",
        default=None,
        help=(
            "Directory for working copies of fixtures. "
            "Defaults to a system-managed temporary directory that is removed after the run."
        ),
    )
    parser.add_argument(
        "--keep-work-dir",
        action="store_true",
        help="Preserve the working directory after the test run for inspection.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print full output from apply and validate steps.",
    )
    return parser.parse_args()


def find_bootstrap_root(script_path):
    """Derive the bootstrap repo root from this script's location (scripts/ -> parent)."""
    scripts_dir = os.path.dirname(os.path.abspath(script_path))
    return os.path.dirname(scripts_dir)


def copy_fixture(fixture_name, bootstrap_root, dest_parent):
    """
    Copy a canonical fixture directory to dest_parent/fixture_name.
    Removes any existing copy first. Returns the destination path.
    """
    source = os.path.join(bootstrap_root, FIXTURES_TARGETS_DIR, fixture_name)
    dest = os.path.join(dest_parent, fixture_name)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(source, dest)
    return dest


def run_apply(bootstrap_root, target_dir):
    """
    Run apply_bootstrap.py against target_dir.
    Returns (returncode, combined_output).
    """
    script = os.path.join(bootstrap_root, "scripts", "apply_bootstrap.py")
    result = subprocess.run(
        [sys.executable, script, "--target-dir", target_dir],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout + result.stderr


def run_validate(bootstrap_root, target_dir):
    """
    Run validate_bootstrap.py --target-dir against target_dir.
    Returns (returncode, combined_output).
    """
    script = os.path.join(bootstrap_root, "scripts", "validate_bootstrap.py")
    result = subprocess.run(
        [sys.executable, script, "--target-dir", target_dir],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout + result.stderr


def load_population_data(bootstrap_root, fixture_name):
    """
    Load the population JSON for a fixture.
    Returns the parsed dict, or None if no population file exists.
    """
    pop_path = os.path.join(
        bootstrap_root, FIXTURES_POPULATION_DIR, f"{fixture_name}.json"
    )
    if not os.path.isfile(pop_path):
        return None
    with open(pop_path, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_population(target_dir, population_data):
    """
    Apply population data to move a scaffolded target from State B to State C.

    Replaces {{PLACEHOLDER_NAME}} markers in the standard placeholder files
    using the 'placeholder_values' mapping in the population data.

    Any 'file_overrides' entries replace an entire file with provided content.
    """
    placeholder_values = population_data.get("placeholder_values", {})
    file_overrides = population_data.get("file_overrides", {})

    # Apply whole-file overrides first
    for rel_path, content in file_overrides.items():
        full_path = os.path.join(target_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

    # Apply placeholder substitutions to the standard placeholder files
    if placeholder_values:
        for rel_path in TARGET_PLACEHOLDER_FILES:
            full_path = os.path.join(target_dir, rel_path)
            if not os.path.isfile(full_path):
                continue
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            for name, value in placeholder_values.items():
                content = content.replace("{{" + name + "}}", value)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)


def count_remaining_placeholders(target_dir):
    """
    Count unfilled {{PLACEHOLDER}} markers across TARGET_PLACEHOLDER_FILES.
    Returns total count and a dict of {rel_path: [marker, ...]} for non-empty files.
    """
    total = 0
    detail = {}
    for rel_path in TARGET_PLACEHOLDER_FILES:
        full_path = os.path.join(target_dir, rel_path)
        if not os.path.isfile(full_path):
            continue
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        found = PLACEHOLDER_RE.findall(content)
        if found:
            detail[rel_path] = sorted(set(found))
            total += len(found)
    return total, detail


def print_indented(text, indent="    "):
    """Print multi-line text with consistent indentation."""
    for line in text.rstrip().splitlines():
        print(f"{indent}{line}")


def test_fixture(fixture_name, bootstrap_root, work_root, args):
    """
    Run State B and (optionally) State C tests for one fixture.

    Returns a dict:
      {
        "name": str,
        "state_b_pass": bool,
        "state_c_pass": bool or None (None = skipped),
        "note": str,
      }
    """
    print(f"\n{'─' * 60}")
    print(f"  Fixture: {fixture_name}")
    print(f"{'─' * 60}")

    fixture_source = os.path.join(bootstrap_root, FIXTURES_TARGETS_DIR, fixture_name)
    if not os.path.isdir(fixture_source):
        print(f"  [ERROR] Fixture directory not found: {fixture_source}")
        return {"name": fixture_name, "state_b_pass": False, "state_c_pass": False,
                "note": "fixture directory missing"}

    # ── State B: scaffold applied, placeholders expected ─────────────────────
    print(f"\n  State B — scaffold applied (placeholders expected)")
    work_b = copy_fixture(fixture_name, bootstrap_root, os.path.join(work_root, "state-b"))

    rc_apply, out_apply = run_apply(bootstrap_root, work_b)
    if args.verbose:
        print_indented(out_apply)

    if rc_apply != 0:
        print(f"  [FAIL] apply_bootstrap.py exited {rc_apply}")
        if not args.verbose:
            print_indented(out_apply)
        return {"name": fixture_name, "state_b_pass": False, "state_c_pass": False,
                "note": f"apply failed (exit {rc_apply})"}

    created_count = out_apply.count("[CREATED]")
    print(f"  apply  : {created_count} file(s) created  [OK]")

    rc_val_b, out_val_b = run_validate(bootstrap_root, work_b)
    remaining_b, detail_b = count_remaining_placeholders(work_b)
    if args.verbose:
        print_indented(out_val_b)

    # State B: validation is EXPECTED to fail because placeholders remain
    state_b_pass = rc_val_b != 0 and remaining_b > 0
    if state_b_pass:
        print(f"  validate (State B): {remaining_b} unfilled placeholder(s) — EXPECTED  [OK]")
    else:
        if rc_val_b == 0:
            print(f"  [UNEXPECTED] State B passed validation — expected placeholder failures")
        else:
            print(f"  [FAIL] State B: unexpected result (remaining={remaining_b}, rc={rc_val_b})")
        if not args.verbose:
            print_indented(out_val_b)

    if args.state_b_only:
        return {"name": fixture_name, "state_b_pass": state_b_pass, "state_c_pass": None,
                "note": "state-b-only mode"}

    # ── State C: minimally populated, validation should pass ─────────────────
    print(f"\n  State C — minimally populated (validation should pass)")
    population_data = load_population_data(bootstrap_root, fixture_name)
    if population_data is None:
        print(f"  [SKIP] No population data found at {FIXTURES_POPULATION_DIR}/{fixture_name}.json")
        return {"name": fixture_name, "state_b_pass": state_b_pass, "state_c_pass": None,
                "note": "no population data"}

    work_c = copy_fixture(fixture_name, bootstrap_root, os.path.join(work_root, "state-c"))

    rc_apply_c, out_apply_c = run_apply(bootstrap_root, work_c)
    if rc_apply_c != 0:
        print(f"  [FAIL] apply failed for State C (exit {rc_apply_c})")
        if args.verbose:
            print_indented(out_apply_c)
        return {"name": fixture_name, "state_b_pass": state_b_pass, "state_c_pass": False,
                "note": f"apply failed for state-c (exit {rc_apply_c})"}

    apply_population(work_c, population_data)

    remaining_c, detail_c = count_remaining_placeholders(work_c)
    if remaining_c > 0:
        print(f"  [WARN] {remaining_c} placeholder(s) still remain after population:")
        for path, markers in detail_c.items():
            print(f"         {path}: {', '.join(markers)}")

    rc_val_c, out_val_c = run_validate(bootstrap_root, work_c)
    if args.verbose:
        print_indented(out_val_c)

    state_c_pass = rc_val_c == 0
    if state_c_pass:
        print(f"  validate (State C): PASSED  [OK]")
    else:
        print(f"  validate (State C): FAILED")
        if not args.verbose:
            print_indented(out_val_c)

    return {"name": fixture_name, "state_b_pass": state_b_pass, "state_c_pass": state_c_pass,
            "note": ""}


def main():
    args = parse_args()
    bootstrap_root = find_bootstrap_root(sys.argv[0])

    fixtures_to_test = [args.fixture] if args.fixture else list(ALL_FIXTURES)

    # Validate requested fixture name(s)
    for name in fixtures_to_test:
        if name not in ALL_FIXTURES:
            print(f"ERROR: Unknown fixture '{name}'. Available: {', '.join(ALL_FIXTURES)}",
                  file=sys.stderr)
            sys.exit(1)

    # Set up working directory
    managed_tmp = args.work_dir is None
    if managed_tmp:
        work_root = tempfile.mkdtemp(prefix="bootstrap-selftest-")
    else:
        work_root = os.path.abspath(args.work_dir)
        os.makedirs(work_root, exist_ok=True)

    print(f"Bootstrap self-test")
    print(f"  Bootstrap root : {bootstrap_root}")
    print(f"  Work directory : {work_root}")
    print(f"  Fixtures       : {', '.join(fixtures_to_test)}")
    print(f"  Mode           : {'State B only' if args.state_b_only else 'State B + State C'}")

    results = []
    try:
        for fixture_name in fixtures_to_test:
            result = test_fixture(fixture_name, bootstrap_root, work_root, args)
            results.append(result)
    finally:
        if managed_tmp and not args.keep_work_dir:
            shutil.rmtree(work_root, ignore_errors=True)
        else:
            print(f"\nWorking directory preserved: {work_root}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'═' * 60}")
    print("  Summary")
    print(f"{'═' * 60}")

    all_pass = True
    for r in results:
        b_label = "PASS" if r["state_b_pass"] else "FAIL"
        if r["state_c_pass"] is None:
            c_label = "SKIP"
        elif r["state_c_pass"]:
            c_label = "PASS"
        else:
            c_label = "FAIL"
            all_pass = False
        if not r["state_b_pass"]:
            all_pass = False
        note_str = f"  ({r['note']})" if r["note"] else ""
        print(f"  {r['name']:<40s}  B:{b_label}  C:{c_label}{note_str}")

    print()
    if all_pass:
        print("SELF-TEST PASSED.")
        sys.exit(0)
    else:
        print("SELF-TEST FAILED. Review output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
