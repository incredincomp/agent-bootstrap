#!/usr/bin/env python3
"""
refresh_bootstrap.py

Refreshes or upgrades an already-bootstrapped target repository to align with
the current canonical bootstrap source templates.

Safe by default — never blindly overwrites repo-specific populated content.
Classifies each managed file and takes only clearly safe actions unless
--force is explicitly provided.

File classifications:
  missing        — file not present in target → will be created
  unchanged      — file matches current template exactly → no action needed
  safe-refresh   — file exists, differs from template, but still has unfilled
                   {{PLACEHOLDER}} markers → can re-apply safely (no local content yet)
  populated      — file has been filled with real content (no remaining
                   {{PLACEHOLDER}} markers) → skipped by default; requires --force
  error          — file could not be read

Default actions (without --force):
  missing        → created
  unchanged      → skipped (already current)
  safe-refresh   → refreshed (template updated since scaffold was applied)
  populated      → skipped and flagged for manual review

With --force:
  populated      → overwritten (destructive; use with care)

Usage:
    python scripts/refresh_bootstrap.py --target-dir /path/to/target-repo
    python scripts/refresh_bootstrap.py --target-dir /path/to/target-repo --dry-run
    python scripts/refresh_bootstrap.py --target-dir /path/to/target-repo --force
    python scripts/refresh_bootstrap.py --target-dir /path/to/target-repo --dry-run --force

Exit codes:
    0 — refresh completed (or dry-run completed) successfully
    1 — critical error (missing bootstrap source, unreadable template, etc.)
"""

import argparse
import datetime
import os
import re
import subprocess
import sys

# Shared bootstrap semantics — profiles, template mappings, marker parsing,
# placeholder detection, version reading.
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPTS_DIR)
from bootstrap_core import (  # noqa: E402
    PLACEHOLDER_RE,
    PROFILES,
    DEFAULT_PROFILE,
    read_version as _core_read_version,
    resolve_template_mappings,
    get_bootstrap_marker_path,
    parse_bootstrap_marker,
    has_placeholders,
)

# Bootstrap marker path within a target repo (kept for local reference).
BOOTSTRAP_MARKER_PATH = "bootstrap/BOOTSTRAP_SOURCE.md"

# ─────────────────────────────────────────────────────────────────────────────
# Template → target-path mappings with refresh classification policy.
#
# refresh_policy values:
#   "safe-if-unpopulated"  — refresh when file still has unfilled placeholders
#                            (structural/scaffold file not yet agent-populated)
#   "manual-review"        — populated repo-specific file; skip by default
#   "marker"               — bootstrap origin marker; compared after rendering
# ─────────────────────────────────────────────────────────────────────────────
TEMPLATE_MAPPINGS = [
    {
        "source": "templates/AGENTS.md.template",
        "destination": "AGENTS.md",
        "description": "Execution contract for AI agents",
        "refresh_policy": "safe-if-unpopulated",
    },
    {
        "source": "templates/IMPLEMENTATION_TRACKER.md.template",
        "destination": "IMPLEMENTATION_TRACKER.md",
        "description": "Live state file — milestones, decisions, validation",
        "refresh_policy": "manual-review",
    },
    {
        "source": "templates/docs/ai/REPO_MAP.md.template",
        "destination": "docs/ai/REPO_MAP.md",
        "description": "Human + agent-readable repository map",
        "refresh_policy": "safe-if-unpopulated",
    },
    {
        "source": "templates/docs/ai/SOURCE_REFRESH.md.template",
        "destination": "docs/ai/SOURCE_REFRESH.md",
        "description": "Instructions for re-syncing agent knowledge",
        "refresh_policy": "safe-if-unpopulated",
    },
    {
        "source": "templates/docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template",
        "destination": "docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md",
        "description": "Vendor-specific AI knowledge base",
        "refresh_policy": "safe-if-unpopulated",
    },
    {
        "source": "templates/bootstrap/BOOTSTRAP_SOURCE.md.template",
        "destination": "bootstrap/BOOTSTRAP_SOURCE.md",
        "description": "Bootstrap origin marker",
        "refresh_policy": "marker",
    },
    {
        "source": "templates/artifacts/ai/repo_discovery.json.template",
        "destination": "artifacts/ai/repo_discovery.json",
        "description": "Machine-readable discovery artifact",
        "refresh_policy": "manual-review",
    },
]

# Placeholders filled automatically in the bootstrap marker file
MARKER_PLACEHOLDERS = {
    "{{BOOTSTRAP_SOURCE_REPO}}": "https://github.com/incredincomp/agent-bootstrap",
    "{{BOOTSTRAP_AGENT}}": "refresh_bootstrap.py",
    "{{BOOTSTRAP_PROMPT_USED}}": "scripts/refresh_bootstrap.py",
}


def read_bootstrap_version(bootstrap_root):
    """Read the bootstrap version from the VERSION file. Returns the version string or 'unknown'."""
    version, _err = _core_read_version(bootstrap_root)
    return version if version is not None else "unknown"


def parse_major_version(version_str):
    """Extract the major version integer from a semver string, or None if not parseable."""
    if not version_str:
        return None
    match = re.match(r"^(\d+)\.", version_str)
    if match:
        return int(match.group(1))
    return None


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Refresh or upgrade an already-bootstrapped target repository "
            "to align with the current canonical bootstrap source templates. "
            "Safe by default: only creates missing files and updates files that "
            "still have unfilled template placeholders."
        )
    )
    parser.add_argument(
        "--target-dir",
        required=True,
        help="Path to the bootstrapped target repository root.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing any files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Also overwrite populated files (those with no remaining template "
            "placeholders). Destructive — use with care."
        ),
    )
    parser.add_argument(
        "--bootstrap-version",
        default=None,
        help=(
            "Bootstrap source version to record in the marker when it is refreshed. "
            "Defaults to the version in the VERSION file."
        ),
    )
    return parser.parse_args()


def find_bootstrap_root(script_path):
    """Derive the bootstrap repo root from this script's location (scripts/ -> parent)."""
    scripts_dir = os.path.dirname(os.path.abspath(script_path))
    return os.path.dirname(scripts_dir)


def get_git_sha(repo_dir):
    """Return the short git HEAD SHA for the bootstrap repo, or 'unknown'."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            capture_output=True,
            text=True,
            cwd=repo_dir,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except OSError:
        pass
    return "unknown"


def render_marker(content, bootstrap_version, bootstrap_revision, refresh_date, profile):
    """Replace bootstrap-system placeholders in the marker template."""
    result = content
    for placeholder, value in MARKER_PLACEHOLDERS.items():
        result = result.replace(placeholder, value)
    result = result.replace("{{BOOTSTRAP_SOURCE_VERSION}}", bootstrap_version)
    result = result.replace("{{BOOTSTRAP_SOURCE_REVISION}}", bootstrap_revision)
    result = result.replace("{{BOOTSTRAP_DATE}}", refresh_date)
    result = result.replace("{{BOOTSTRAP_PROFILE}}", profile)
    return result


def resolve_mappings(profile_name):
    """
    Return the effective template mappings for the given profile.

    Starts from the common TEMPLATE_MAPPINGS and applies any profile-specific
    source overrides for the given profile.  Falls back to 'generic' if the
    profile is not recognised.
    """
    # Preserve refresh_policy fields by merging with the refresh-specific policy map
    refresh_policies = {m["destination"]: m["refresh_policy"] for m in TEMPLATE_MAPPINGS}
    resolved_base = resolve_template_mappings(
        profile_name if profile_name in PROFILES else DEFAULT_PROFILE
    )
    return [{**m, "refresh_policy": refresh_policies.get(m["destination"], "safe-if-unpopulated")}
            for m in resolved_base]


def detect_bootstrap_state(target_dir):
    """
    Detect whether the target directory was previously bootstrapped.

    Returns a dict:
      {
        "is_bootstrapped": bool,
        "marker_path": str or None,     # absolute path to marker if present
        "bootstrap_version": str or None,
        "bootstrap_date": str or None,
        "bootstrap_profile": str or None,
      }
    """
    marker_abs = os.path.join(target_dir, BOOTSTRAP_MARKER_PATH)
    if not os.path.isfile(marker_abs):
        return {
            "is_bootstrapped": False,
            "marker_path": None,
            "bootstrap_version": None,
            "bootstrap_date": None,
            "bootstrap_profile": None,
        }

    version = None
    date = None
    profile = None
    try:
        with open(marker_abs, "r", encoding="utf-8") as f:
            for line in f:
                # Look for table rows like: | Bootstrap source version | abc123 |
                if "Bootstrap source version" in line:
                    parts = [p.strip() for p in line.strip().strip("|").split("|")]
                    if len(parts) >= 2:
                        candidate = parts[-1].strip()
                        if candidate and candidate != "{{BOOTSTRAP_SOURCE_VERSION}}":
                            version = candidate
                if "Bootstrap date" in line:
                    parts = [p.strip() for p in line.strip().strip("|").split("|")]
                    if len(parts) >= 2:
                        candidate = parts[-1].strip()
                        if candidate and candidate != "{{BOOTSTRAP_DATE}}":
                            date = candidate
                if "Bootstrap profile" in line:
                    parts = [p.strip() for p in line.strip().strip("|").split("|")]
                    if len(parts) >= 2:
                        candidate = parts[-1].strip()
                        if candidate and candidate != "{{BOOTSTRAP_PROFILE}}":
                            profile = candidate
    except OSError:
        pass

    return {
        "is_bootstrapped": True,
        "marker_path": marker_abs,
        "bootstrap_version": version,
        "bootstrap_date": date,
        "bootstrap_profile": profile,
    }


def classify_file(template_content, dest_path, refresh_policy):
    """
    Classify a managed file to determine the appropriate refresh action.

    Returns one of:
      'missing'       — file does not exist in target
      'unchanged'     — file exists and content matches current template exactly
      'safe-refresh'  — file differs from template but still has unfilled
                        {{PLACEHOLDER}} markers (unpopulated scaffold)
      'populated'     — file has no unfilled {{PLACEHOLDER}} markers
                        (repo-specific content has been filled in)
      'error:...'     — file could not be read
    """
    if not os.path.isfile(dest_path):
        return "missing"

    try:
        with open(dest_path, "r", encoding="utf-8") as f:
            current_content = f.read()
    except OSError as exc:
        return f"error:could not read file: {exc}"

    if current_content == template_content:
        return "unchanged"

    # Check for remaining unfilled placeholders as signal of unpopulated state
    if has_placeholders(current_content):
        return "safe-refresh"

    return "populated"


def write_file(dest_path, content):
    """Write content to dest_path, creating parent directories as needed."""
    dest_dir = os.path.dirname(dest_path)
    if dest_dir:
        os.makedirs(dest_dir, exist_ok=True)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    args = parse_args()

    bootstrap_root = find_bootstrap_root(sys.argv[0])
    target_dir = os.path.abspath(args.target_dir)

    if not os.path.isdir(target_dir):
        print(f"ERROR: Target directory does not exist: {target_dir}", file=sys.stderr)
        sys.exit(1)

    bootstrap_version = args.bootstrap_version or read_bootstrap_version(bootstrap_root)
    bootstrap_revision = get_git_sha(bootstrap_root)
    refresh_date = datetime.datetime.now(datetime.timezone.utc).date().isoformat()

    mode_label = "[DRY RUN] " if args.dry_run else ""
    print(f"{mode_label}Bootstrap refresh")
    print(f"  Bootstrap source  : {bootstrap_root}")
    print(f"  Bootstrap version : {bootstrap_version}")
    print(f"  Bootstrap revision: {bootstrap_revision}")
    print(f"  Target directory  : {target_dir}")
    print(f"  Force mode        : {'yes (will overwrite populated files)' if args.force else 'no (safe defaults)'}")
    print()

    # ── Detect bootstrap state ───────────────────────────────────────────────
    state = detect_bootstrap_state(target_dir)
    if state["is_bootstrapped"]:
        print(f"  Bootstrap marker  : detected ({BOOTSTRAP_MARKER_PATH})")
        if state["bootstrap_version"]:
            print(f"  Prior version     : {state['bootstrap_version']}")
        if state["bootstrap_date"]:
            print(f"  Prior date        : {state['bootstrap_date']}")
        if state["bootstrap_profile"]:
            print(f"  Prior profile     : {state['bootstrap_profile']}")
    else:
        print(
            f"  Bootstrap marker  : not found — "
            f"target may not have been bootstrapped yet (consider apply_bootstrap.py)"
        )
    print()

    # ── Major-version drift warning ──────────────────────────────────────────
    prior_version = state.get("bootstrap_version")
    if prior_version:
        current_major = parse_major_version(bootstrap_version)
        prior_major = parse_major_version(prior_version)
        if current_major is not None and prior_major is not None and current_major != prior_major:
            print(
                f"  [WARN] Major-version drift detected: "
                f"target was bootstrapped from v{prior_version}, "
                f"current bootstrap is v{bootstrap_version}."
            )
            print(
                "  [WARN] Major version changes may require manual review before applying."
            )
            print(
                "  [WARN] Consider running with --dry-run first and reviewing the planned changes."
            )
            print()

    # Resolve profile from marker; fall back to generic if not recorded
    current_profile = state.get("bootstrap_profile") or DEFAULT_PROFILE
    if current_profile not in PROFILES:
        print(
            f"  [WARN] Unrecognised profile '{current_profile}' in marker — "
            f"falling back to '{DEFAULT_PROFILE}'."
        )
        current_profile = DEFAULT_PROFILE
    print(f"  Using profile     : {current_profile}")
    print()

    # ── Classify and process each managed file ───────────────────────────────
    results = {
        "created": [],
        "unchanged": [],
        "refreshed": [],
        "skipped-populated": [],
        "would-create": [],
        "would-refresh": [],
        "would-overwrite": [],
        "errors": [],
    }

    effective_mappings = resolve_mappings(current_profile)

    for mapping in effective_mappings:
        source_path = os.path.join(bootstrap_root, mapping["source"])
        dest_path = os.path.join(target_dir, mapping["destination"])
        dest_label = mapping["destination"]
        policy = mapping["refresh_policy"]

        if not os.path.isfile(source_path):
            results["errors"].append(
                (dest_label, f"source template not found: {mapping['source']}")
            )
            print(f"  [ERROR] {dest_label} — source template not found: {mapping['source']}")
            continue

        try:
            with open(source_path, "r", encoding="utf-8") as f:
                template_content = f.read()
        except OSError as exc:
            results["errors"].append((dest_label, f"could not read template: {exc}"))
            print(f"  [ERROR] {dest_label} — could not read template: {exc}")
            continue

        # For the marker, compare against the rendered version
        compare_content = template_content
        write_content = template_content
        if policy == "marker":
            compare_content = render_marker(template_content, bootstrap_version, bootstrap_revision, refresh_date, current_profile)
            write_content = compare_content

        classification = classify_file(compare_content, dest_path, policy)

        if classification.startswith("error:"):
            msg = classification[len("error:"):]
            results["errors"].append((dest_label, msg))
            print(f"  [ERROR] {dest_label} — {msg}")
            continue

        # ── Determine action based on classification and policy ──────────────
        if classification == "missing":
            if args.dry_run:
                results["would-create"].append(dest_label)
                print(f"  [WOULD CREATE]   {dest_label}")
            else:
                try:
                    write_file(dest_path, write_content)
                    results["created"].append(dest_label)
                    print(f"  [CREATED]        {dest_label}")
                except OSError as exc:
                    results["errors"].append((dest_label, str(exc)))
                    print(f"  [ERROR]          {dest_label} — {exc}")

        elif classification == "unchanged":
            results["unchanged"].append(dest_label)
            print(f"  [UNCHANGED]      {dest_label}")

        elif classification == "safe-refresh":
            # Safe to refresh — file still has unfilled template placeholders
            if args.dry_run:
                results["would-refresh"].append(dest_label)
                print(f"  [WOULD REFRESH]  {dest_label}  (has unfilled placeholders)")
            else:
                try:
                    write_file(dest_path, write_content)
                    results["refreshed"].append(dest_label)
                    print(f"  [REFRESHED]      {dest_label}  (had unfilled placeholders)")
                except OSError as exc:
                    results["errors"].append((dest_label, str(exc)))
                    print(f"  [ERROR]          {dest_label} — {exc}")

        elif classification == "populated":
            # File has repo-specific content filled — skip unless --force
            if args.force:
                if args.dry_run:
                    results["would-overwrite"].append(dest_label)
                    print(f"  [WOULD OVERWRITE] {dest_label}  (populated — --force)")
                else:
                    try:
                        write_file(dest_path, write_content)
                        results["refreshed"].append(dest_label)
                        print(f"  [OVERWRITTEN]    {dest_label}  (populated — --force)")
                    except OSError as exc:
                        results["errors"].append((dest_label, str(exc)))
                        print(f"  [ERROR]          {dest_label} — {exc}")
            else:
                results["skipped-populated"].append(dest_label)
                print(
                    f"  [SKIPPED]        {dest_label}  "
                    f"(populated — manual review; use --force to overwrite)"
                )

    # ── Print summary ─────────────────────────────────────────────────────────
    print()
    print("=== Refresh summary ===")
    if args.dry_run:
        print(f"  Would create       : {len(results['would-create'])}")
        print(f"  Would refresh      : {len(results['would-refresh'])}")
        print(f"  Would overwrite    : {len(results['would-overwrite'])}")
        print(f"  Unchanged          : {len(results['unchanged'])}")
        print(f"  Skipped (populated): {len(results['skipped-populated'])}")
    else:
        print(f"  Created            : {len(results['created'])}")
        print(f"  Refreshed          : {len(results['refreshed'])}")
        print(f"  Unchanged          : {len(results['unchanged'])}")
        print(f"  Skipped (populated): {len(results['skipped-populated'])}")
    print(f"  Errors             : {len(results['errors'])}")

    if results["skipped-populated"]:
        print()
        print("Files skipped (populated — require manual review or --force):")
        for path in results["skipped-populated"]:
            print(f"    {path}")

    if results["errors"]:
        print()
        print("Errors encountered — review output above.")
        sys.exit(1)

    print()
    if args.dry_run:
        total_changes = (
            len(results["would-create"])
            + len(results["would-refresh"])
            + len(results["would-overwrite"])
        )
        if total_changes == 0:
            print("Dry run: no changes would be made.")
        else:
            print(
                f"Dry run: {total_changes} file(s) would change. "
                "Re-run without --dry-run to apply."
            )
        if results["skipped-populated"] and not args.force:
            print(
                f"  {len(results['skipped-populated'])} populated file(s) would be skipped. "
                "Add --force to overwrite them."
            )
    else:
        total_changed = len(results["created"]) + len(results["refreshed"])
        if total_changed > 0:
            print("Refresh complete.")
            print()
            print("Recommended next step:")
            print(
                f"  python scripts/validate_bootstrap.py --target-dir {target_dir}"
            )
        else:
            print("No files changed — target is already current.")
            if results["skipped-populated"]:
                print(
                    "  Populated files were skipped. Review them manually or use --force."
                )

    sys.exit(0)


if __name__ == "__main__":
    main()
