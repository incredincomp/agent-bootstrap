#!/usr/bin/env python3
"""
bulk_audit.py

Read-only bulk multi-repo audit tool.

Inspects multiple target repositories and produces an aggregate health
summary using the stabilised bootstrap doctor JSON contract.

Usage:
    python scripts/bulk_audit.py --repo /path/to/repo-a --repo /path/to/repo-b
    python scripts/bulk_audit.py --root-dir /path/to/repos
    python scripts/bulk_audit.py --root-dir /path/to/repos --max-depth 2
    python scripts/bulk_audit.py --root-dir /path/to/repos --json
    python scripts/bulk_audit.py --repo /path/to/repo-a --json --output /tmp/bulk.json

Exit codes:
    0 — report produced (even if some repos are unhealthy)
    1 — operational error (no repos found, unreadable output path, etc.)

Repo discovery under --root-dir:
    Only directories containing a '.git/' subdirectory are treated as
    repositories.  This is conservative and deliberate — do not change
    to a glob-based discovery without an explicit policy decision.

This tool is read-only.  It never creates, modifies, or deletes files.
"""

import argparse
import datetime
import json
import os
import sys

# Shared bootstrap semantics
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPTS_DIR)

import bootstrap_doctor as bd              # noqa: E402
from bootstrap_core import read_version   # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# Bulk report schema version — tracks the shape of this tool's JSON contract.
# Independent of the bootstrap repo VERSION file.
#   patch — additive optional fields
#   minor — new required fields or new enum values
#   major — renamed/removed required fields or semantically breaking changes
# ─────────────────────────────────────────────────────────────────────────────
BULK_REPORT_SCHEMA_VERSION = "1.0.0"

# Stable health-state names (mirrored from bootstrap_doctor — do not rename).
ALL_HEALTH_STATES = [
    "populated-and-healthy",
    "stale-version-review-recommended",
    "profile-mismatch-review-recommended",
    "partially-populated",
    "scaffold-applied-unpopulated",
    "unbootstrapped",
]

# States that warrant attention in the high-priority summary.
HIGH_PRIORITY_STATES = {
    "stale-version-review-recommended",
    "profile-mismatch-review-recommended",
    "partially-populated",
    "unbootstrapped",
}

# Sort key for health states not in HIGH_PRIORITY_STATES (treated as lowest priority).
_UNKNOWN_PRIORITY = len(HIGH_PRIORITY_STATES) + 1


# ─────────────────────────────────────────────────────────────────────────────
# Repo discovery
# ─────────────────────────────────────────────────────────────────────────────

def discover_repos(root_dir, max_depth=1):
    """
    Discover candidate repositories under root_dir.

    A candidate is any immediate subdirectory (up to max_depth levels deep)
    that contains a '.git/' directory.  This is conservative — only directories
    that are clearly git repos are included.

    Returns a sorted list of absolute paths.
    """
    root_dir = os.path.abspath(root_dir)
    found = []
    _walk_for_repos(root_dir, root_dir, max_depth, 0, found)
    return sorted(found)


def _walk_for_repos(base, current, max_depth, depth, found):
    """Recursively walk directories up to max_depth, collecting git repos."""
    if depth > max_depth:
        return
    try:
        entries = os.listdir(current)
    except OSError:
        return
    if depth > 0 and ".git" in entries and os.path.isdir(os.path.join(current, ".git")):
        found.append(current)
        return  # don't recurse into nested git repos
    if depth < max_depth:
        for entry in sorted(entries):
            full = os.path.join(current, entry)
            if os.path.isdir(full) and not entry.startswith("."):
                _walk_for_repos(base, full, max_depth, depth + 1, found)


# ─────────────────────────────────────────────────────────────────────────────
# Per-repo audit
# ─────────────────────────────────────────────────────────────────────────────

def audit_repo(target_dir, bootstrap_root):
    """
    Run the doctor audit on a single target repo.

    target_dir may be any existing directory — it does not need to contain
    a .git/ subdirectory.  Repos without a bootstrap marker are classified
    as 'unbootstrapped'.  This is in contrast to --root-dir discovery, which
    only picks up directories that contain .git/.

    Returns (result_dict, None) on success, or (None, error_string) on failure.
    result_dict is the full structured dict from bootstrap_doctor.audit().
    On failure the caller is expected to record the error and continue
    processing other repos — one failure must not stop the bulk run.
    """
    try:
        target_dir = os.path.abspath(target_dir)
        if not os.path.isdir(target_dir):
            return None, f"not a directory: {target_dir}"
        result = bd.audit(target_dir, bootstrap_root)
        return result, None
    except (OSError, ValueError) as exc:
        return None, str(exc)
    except Exception as exc:  # noqa: BLE001 — guard: continue fleet audit despite unexpected errors
        return None, f"unexpected error: {exc}"


# ─────────────────────────────────────────────────────────────────────────────
# Aggregate summary helpers
# ─────────────────────────────────────────────────────────────────────────────

def build_summary(repo_results):
    """
    Build an aggregate summary from a list of per-repo result dicts.

    Returns a dict with counts by health state and by recorded profile.
    """
    by_state = {state: 0 for state in ALL_HEALTH_STATES}
    by_profile = {}

    for result in repo_results:
        state = result.get("health_state", "unbootstrapped")
        by_state[state] = by_state.get(state, 0) + 1

        profile = result.get("recorded_profile") or result.get("suggested_profile") or "generic"
        by_profile[profile] = by_profile.get(profile, 0) + 1

    return {
        "by_health_state": by_state,
        "by_profile": by_profile,
    }


def high_priority_repos(repo_results):
    """Return repos that need attention, sorted by health state priority."""
    priority_order = list(HIGH_PRIORITY_STATES)
    attention = [r for r in repo_results if r.get("health_state") in HIGH_PRIORITY_STATES]
    attention.sort(key=lambda r: priority_order.index(r.get("health_state"))
                   if r.get("health_state") in priority_order else _UNKNOWN_PRIORITY)
    return attention


# ─────────────────────────────────────────────────────────────────────────────
# Human-readable output
# ─────────────────────────────────────────────────────────────────────────────

def print_human_report(repo_results, errors, source_version, repo_paths_requested):
    """Print a concise human-readable bulk audit report."""
    total = len(repo_results) + len(errors)
    print("Bulk Bootstrap Audit")
    print(f"  Bootstrap source version : {source_version or '(unknown)'}")
    print(f"  Repos scanned            : {total}")
    if errors:
        print(f"  Repos with errors        : {len(errors)}")
    print()

    if not repo_results and not errors:
        print("  No repositories found.")
        return

    summary = build_summary(repo_results)

    # Aggregate counts by health state
    print("  Health state summary:")
    for state in ALL_HEALTH_STATES:
        count = summary["by_health_state"].get(state, 0)
        if count > 0 or state in ("populated-and-healthy", "unbootstrapped"):
            marker = " !" if state in HIGH_PRIORITY_STATES and count > 0 else ""
            print(f"    {state:<42} {count:>3}{marker}")
    print()

    # Profile distribution
    if summary["by_profile"]:
        print("  Profile distribution:")
        for profile, count in sorted(summary["by_profile"].items()):
            print(f"    {profile:<30} {count:>3}")
        print()

    # High-priority repos
    attention = high_priority_repos(repo_results)
    if attention:
        print("  Repos needing attention:")
        for r in attention:
            name = os.path.basename(r["target_dir"])
            state = r["health_state"]
            rv = r.get("recorded_version") or "(not recorded)"
            rp = r.get("recorded_profile") or "(not recorded)"
            sp = r.get("suggested_profile", "")
            line = f"    {name} — {state}"
            if state == "stale-version-review-recommended":
                sv = r.get("source_version") or "?"
                line += f" — version {rv} → current {sv}"
            elif state == "profile-mismatch-review-recommended":
                line += f" — recorded {rp}, suggested {sp}"
            elif state == "unbootstrapped":
                line += f" — suggested profile {sp}"
            elif state == "partially-populated":
                n_ph = r.get("total_placeholder_count", 0)
                line += f" — {n_ph} placeholder(s) remaining"
            print(line)
        print()

    # Per-repo concise lines
    print("  Per-repo summary:")
    for r in repo_results:
        name = os.path.basename(r["target_dir"])
        state = r["health_state"]
        rv = r.get("recorded_version") or "(not recorded)"
        rp = r.get("recorded_profile") or r.get("suggested_profile") or "generic"
        print(f"    {name:<30} {state:<42} version {rv}  profile {rp}")

    if errors:
        print()
        print("  Errors (repos skipped):")
        for path, err in errors:
            print(f"    {path}: {err}")

    print()
    print("  Note: This report is advisory only. bulk_audit never modifies any files.")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# Machine-readable JSON output
# ─────────────────────────────────────────────────────────────────────────────

def _str_to_structured_rec(rec):
    """
    Convert a recommendation string to a structured {type, value} object.

    Strings starting with '#' become notes; all others become commands.
    This mirrors the conversion in bootstrap_doctor._recommendations_to_structured()
    and must remain semantically consistent with that function.
    """
    if rec.startswith("#"):
        return {"type": "note", "value": rec[1:].strip()}
    return {"type": "command", "value": rec}


def _repo_result_to_json(result):
    """
    Convert a per-repo audit result dict to a JSON-serialisable object.

    Uses the doctor JSON contract fields as the canonical per-repo shape.
    Structured recommendations use the same {type, value} format as the doctor.
    """
    return {
        "target_dir": result["target_dir"],
        "bootstrapped": result["bootstrapped"],
        "health_state": result["health_state"],
        "marker_status": result["marker_status"],
        "marker_era": result["marker_era"],
        "recorded_version": result.get("recorded_version"),
        "source_version": result.get("source_version"),
        "recorded_profile": result.get("recorded_profile"),
        "suggested_profile": result.get("suggested_profile"),
        "profile_confidence": result.get("profile_confidence"),
        "profile_alignment": result.get("profile_alignment"),
        "required_files_status": result["required_files_status"],
        "missing_files": result.get("missing_files", []),
        "placeholder_status": result["placeholder_status"],
        "files_with_placeholders": result.get("files_with_placeholders", []),
        "total_placeholder_count": result.get("total_placeholder_count", 0),
        "recommendations": [
            _str_to_structured_rec(r) for r in result.get("recommendations", [])
        ],
    }


def build_json_report(repo_results, errors, source_version):
    """
    Build a structured bulk JSON report dict.

    Conforms to schemas/bootstrap_bulk_audit_report.schema.json.
    """
    summary = build_summary(repo_results)
    return {
        "schema_version": BULK_REPORT_SCHEMA_VERSION,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bootstrap_source_version": source_version,
        "repo_count": len(repo_results) + len(errors),
        "summary": summary,
        "repos": [_repo_result_to_json(r) for r in repo_results],
        "errors": [{"repo_path": path, "error": err} for path, err in errors],
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def find_bootstrap_root(script_path):
    """Derive bootstrap repo root from this script's location (scripts/ -> parent)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(script_path)))


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Read-only bulk audit of multiple target repositories. "
            "Produces an aggregate health summary using the bootstrap doctor "
            "JSON contract. Never modifies any repository."
        )
    )
    parser.add_argument(
        "--repo",
        dest="repos",
        action="append",
        default=[],
        metavar="PATH",
        help=(
            "Path to a target repository to audit. May be repeated. "
            "Accepts any existing directory — .git/ is not required. "
            "Use --root-dir to discover repos automatically."
        ),
    )
    parser.add_argument(
        "--root-dir",
        default=None,
        metavar="DIR",
        help=(
            "Parent directory to scan for repositories. "
            "Only directories containing .git/ are treated as repos."
        ),
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=1,
        metavar="N",
        help=(
            "Maximum depth to scan under --root-dir (default: 1, "
            "i.e. immediate subdirectories only)."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output result as JSON instead of human-readable text.",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help="Write JSON output to FILE instead of stdout (requires --json).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    bootstrap_root = find_bootstrap_root(sys.argv[0])
    source_version, _ = read_version(bootstrap_root)

    # Collect explicit repo paths
    repo_paths = list(args.repos)

    # Discover repos under --root-dir
    if args.root_dir:
        root_dir = os.path.abspath(args.root_dir)
        if not os.path.isdir(root_dir):
            print(
                f"ERROR: --root-dir is not a directory: {root_dir}",
                file=sys.stderr,
            )
            sys.exit(1)
        discovered = discover_repos(root_dir, max_depth=args.max_depth)
        repo_paths.extend(discovered)

    # Deduplicate while preserving order
    seen = set()
    unique_paths = []
    for p in repo_paths:
        p = os.path.abspath(p)
        if p not in seen:
            seen.add(p)
            unique_paths.append(p)

    if not unique_paths:
        if not args.repos and not args.root_dir:
            print(
                "ERROR: no repositories specified. "
                "Use --repo or --root-dir to provide target repos.",
                file=sys.stderr,
            )
        elif args.root_dir:
            print(
                f"ERROR: no git repositories found under {args.root_dir} "
                f"(scanned {args.max_depth} level(s) deep; "
                "only directories containing .git/ are treated as repos).",
                file=sys.stderr,
            )
        else:
            print(
                "ERROR: no valid repositories found.",
                file=sys.stderr,
            )
        sys.exit(1)

    # Audit each repo
    repo_results = []
    errors = []
    for path in unique_paths:
        result, err = audit_repo(path, bootstrap_root)
        if err:
            errors.append((path, err))
        else:
            repo_results.append(result)

    # Output
    if args.json_output:
        report = build_json_report(repo_results, errors, source_version)
        output_text = json.dumps(report, indent=2)
        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(output_text)
                    f.write("\n")
            except OSError as exc:
                print(f"ERROR: cannot write output file: {exc}", file=sys.stderr)
                sys.exit(1)
        else:
            print(output_text)
    else:
        print_human_report(repo_results, errors, source_version, unique_paths)


if __name__ == "__main__":
    main()
