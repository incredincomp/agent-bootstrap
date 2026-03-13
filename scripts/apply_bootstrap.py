#!/usr/bin/env python3
"""
apply_bootstrap.py

Applies the canonical agent-bootstrap scaffold into a target repository.

This script stages the required directory structure and template files into a
target repo so that an agent (or human) can then inspect the target repo and
fill those files with real, evidence-based content.

It does NOT auto-populate repo-specific content. That step remains agent-led,
using the discovery and bootstrap prompts.

Usage:
    python scripts/apply_bootstrap.py --target-dir /path/to/target-repo
    python scripts/apply_bootstrap.py --target-dir /path/to/target-repo --dry-run
    python scripts/apply_bootstrap.py --target-dir /path/to/target-repo --force

Exit codes:
    0 — successful apply or dry-run (even if some files were skipped)
    1 — critical error (missing bootstrap source, unreadable manifest, etc.)
"""

import argparse
import datetime
import os
import shutil
import sys

# ─────────────────────────────────────────────────────────────────────────────
# Supported profiles.
#
# Each profile entry may define 'template_overrides': a mapping from
# destination path → source template path (relative to the bootstrap repo root)
# that replaces the common template for that destination.
#
# Generic uses all common templates with no overrides.
# Other profiles override specific templates where profile-specific guidance
# materially improves usefulness for that repo family.
# ─────────────────────────────────────────────────────────────────────────────
PROFILES = {
    "generic": {
        "description": "General-purpose profile. Uses all common templates with no overrides.",
        "template_overrides": {},
    },
    "python-service": {
        "description": (
            "Python service repositories. Adds Python-specific guidance "
            "in the vendor knowledge base."
        ),
        "template_overrides": {
            "docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md": (
                "templates/profiles/python-service/docs/ai/"
                "AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template"
            ),
        },
    },
    "infra-repo": {
        "description": (
            "Infrastructure/platform repositories (Terraform, Pulumi, Ansible, etc.). "
            "Adds infrastructure-specific guidance in the vendor knowledge base."
        ),
        "template_overrides": {
            "docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md": (
                "templates/profiles/infra-repo/docs/ai/"
                "AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template"
            ),
        },
    },
    "vscode-extension": {
        "description": (
            "VS Code extension repositories. Adds extension-specific guidance "
            "in the vendor knowledge base."
        ),
        "template_overrides": {
            "docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md": (
                "templates/profiles/vscode-extension/docs/ai/"
                "AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template"
            ),
        },
    },
    "kubernetes-platform": {
        "description": (
            "Kubernetes platform and operator repositories. Adds platform-specific "
            "guidance in the vendor knowledge base."
        ),
        "template_overrides": {
            "docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md": (
                "templates/profiles/kubernetes-platform/docs/ai/"
                "AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template"
            ),
        },
    },
}

DEFAULT_PROFILE = "generic"

# ─────────────────────────────────────────────────────────────────────────────
# Template → target-path mappings driven by bootstrap-manifest.yaml entries.
# We keep a static fallback here so the script works even if manifest parsing
# is extended later.  The source paths are relative to the bootstrap repo root.
# ─────────────────────────────────────────────────────────────────────────────
TEMPLATE_MAPPINGS = [
    {
        "source": "templates/AGENTS.md.template",
        "destination": "AGENTS.md",
        "description": "Execution contract for AI agents",
    },
    {
        "source": "templates/IMPLEMENTATION_TRACKER.md.template",
        "destination": "IMPLEMENTATION_TRACKER.md",
        "description": "Live state file — milestones, decisions, validation",
    },
    {
        "source": "templates/docs/ai/REPO_MAP.md.template",
        "destination": "docs/ai/REPO_MAP.md",
        "description": "Human + agent-readable repository map",
    },
    {
        "source": "templates/docs/ai/SOURCE_REFRESH.md.template",
        "destination": "docs/ai/SOURCE_REFRESH.md",
        "description": "Instructions for re-syncing agent knowledge",
    },
    {
        "source": "templates/docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template",
        "destination": "docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md",
        "description": "Vendor-specific AI knowledge base",
    },
    {
        "source": "templates/bootstrap/BOOTSTRAP_SOURCE.md.template",
        "destination": "bootstrap/BOOTSTRAP_SOURCE.md",
        "description": "Bootstrap origin marker",
    },
    {
        "source": "templates/artifacts/ai/repo_discovery.json.template",
        "destination": "artifacts/ai/repo_discovery.json",
        "description": "Machine-readable discovery artifact",
    },
]

# Placeholders replaced in the bootstrap marker file only.
# These are bootstrap-system values, not repo-specific discovery content.
MARKER_PLACEHOLDERS = {
    "{{BOOTSTRAP_SOURCE_REPO}}": "https://github.com/incredincomp/agent-bootstrap",
    "{{BOOTSTRAP_AGENT}}": "apply_bootstrap.py",
    "{{BOOTSTRAP_PROMPT_USED}}": "scripts/apply_bootstrap.py",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Apply the canonical agent-bootstrap scaffold into a target repository. "
            "Stages template files so an agent can then populate them with real "
            "repo-specific content."
        )
    )
    parser.add_argument(
        "--target-dir",
        required=True,
        help="Path to the target repository root where bootstrap files will be staged.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created or skipped without writing any files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files. Default behavior skips existing files.",
    )
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        choices=sorted(PROFILES.keys()),
        metavar="PROFILE",
        help=(
            f"Bootstrap profile to apply. Choices: {', '.join(sorted(PROFILES.keys()))}. "
            f"Default: {DEFAULT_PROFILE}."
        ),
    )
    parser.add_argument(
        "--bootstrap-version",
        default=None,
        help=(
            "Bootstrap source version (git SHA, tag, or label) to record in the "
            "marker file. Defaults to the git HEAD SHA of the bootstrap repo."
        ),
    )
    return parser.parse_args()


def resolve_mappings(profile_name, bootstrap_root):
    """
    Return the effective template mappings for the given profile.

    Starts from the common TEMPLATE_MAPPINGS and applies any profile-specific
    source overrides, replacing the template source path for overridden destinations.
    """
    if profile_name not in PROFILES:
        raise ValueError(
            f"Unknown profile '{profile_name}'. "
            f"Supported profiles: {', '.join(sorted(PROFILES.keys()))}"
        )
    overrides = PROFILES[profile_name]["template_overrides"]
    resolved = []
    for mapping in TEMPLATE_MAPPINGS:
        dest = mapping["destination"]
        if dest in overrides:
            resolved.append({**mapping, "source": overrides[dest]})
        else:
            resolved.append(mapping)
    return resolved


def find_bootstrap_root(script_path):
    """Derive the bootstrap repo root from this script's location (scripts/ -> parent)."""
    scripts_dir = os.path.dirname(os.path.abspath(script_path))
    return os.path.dirname(scripts_dir)


def get_git_sha(repo_dir):
    """Return the short git HEAD SHA for the bootstrap repo, or 'unknown'."""
    git_head = os.path.join(repo_dir, ".git", "HEAD")
    if not os.path.isfile(git_head):
        return "unknown"
    try:
        with open(git_head, "r", encoding="utf-8") as f:
            head_content = f.read().strip()
        # Packed ref: ref: refs/heads/...
        if head_content.startswith("ref: "):
            ref_path = head_content[5:]
            packed_ref_file = os.path.join(repo_dir, ".git", ref_path)
            if os.path.isfile(packed_ref_file):
                with open(packed_ref_file, "r", encoding="utf-8") as f:
                    return f.read().strip()[:12]
            # Try packed-refs
            packed_refs = os.path.join(repo_dir, ".git", "packed-refs")
            if os.path.isfile(packed_refs):
                with open(packed_refs, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().endswith(ref_path):
                            return line.split()[0][:12]
        else:
            # Detached HEAD — content is the SHA
            return head_content[:12]
    except OSError:
        pass
    return "unknown"


def render_marker(content, bootstrap_version, apply_date, profile):
    """Replace known bootstrap-system placeholders in the marker file content."""
    result = content
    for placeholder, value in MARKER_PLACEHOLDERS.items():
        result = result.replace(placeholder, value)
    result = result.replace("{{BOOTSTRAP_SOURCE_VERSION}}", bootstrap_version)
    result = result.replace("{{BOOTSTRAP_DATE}}", apply_date)
    result = result.replace("{{BOOTSTRAP_PROFILE}}", profile)
    # BOOTSTRAP_NOTES is intentionally left for the agent to fill
    return result


def ensure_directory(dir_path, dry_run):
    """Create a directory (and parents) if it does not exist."""
    if not os.path.isdir(dir_path):
        if not dry_run:
            os.makedirs(dir_path, exist_ok=True)


def apply_template(source_path, dest_path, mapping, ctx):
    """
    Copy one template file to its destination.

    ctx keys: bootstrap_version, apply_date, dry_run, force.

    Returns a status string: 'created', 'skipped', 'would_overwrite',
    'overwritten', or 'error:<message>'.
    """
    is_marker = mapping["destination"] == "bootstrap/BOOTSTRAP_SOURCE.md"
    dry_run = ctx["dry_run"]
    force = ctx["force"]

    dest_exists = os.path.isfile(dest_path)

    if dest_exists and not force:
        return "skipped"

    if dest_exists and force and dry_run:
        return "would_overwrite"

    try:
        with open(source_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as exc:
        return f"error:could not read source: {exc}"

    if is_marker:
        content = render_marker(content, ctx["bootstrap_version"], ctx["apply_date"], ctx["profile"])

    if dry_run:
        if dest_exists:
            return "would_overwrite"
        return "created"

    dest_dir = os.path.dirname(dest_path)
    if dest_dir:
        os.makedirs(dest_dir, exist_ok=True)

    try:
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as exc:
        return f"error:could not write destination: {exc}"

    if dest_exists:
        return "overwritten"
    return "created"


def main():
    args = parse_args()

    bootstrap_root = find_bootstrap_root(sys.argv[0])
    target_dir = os.path.abspath(args.target_dir)

    if not os.path.isdir(target_dir):
        print(f"ERROR: Target directory does not exist: {target_dir}", file=sys.stderr)
        sys.exit(1)

    profile = args.profile
    if profile not in PROFILES:
        print(
            f"ERROR: Unknown profile '{profile}'. "
            f"Supported profiles: {', '.join(sorted(PROFILES.keys()))}",
            file=sys.stderr,
        )
        sys.exit(1)

    bootstrap_version = args.bootstrap_version or get_git_sha(bootstrap_root)
    apply_date = datetime.datetime.now(datetime.timezone.utc).date().isoformat()

    ctx = {
        "bootstrap_version": bootstrap_version,
        "apply_date": apply_date,
        "dry_run": args.dry_run,
        "force": args.force,
        "profile": profile,
    }

    mode_label = "[DRY RUN] " if args.dry_run else ""
    print(f"{mode_label}Applying bootstrap scaffold")
    print(f"  Bootstrap source : {bootstrap_root}")
    print(f"  Bootstrap version: {bootstrap_version}")
    print(f"  Target directory : {target_dir}")
    print(f"  Profile          : {profile} — {PROFILES[profile]['description']}")
    print(f"  Overwrite mode   : {'--force (overwrite existing)' if args.force else 'safe (skip existing)'}")
    print()

    results = {
        "created": [],
        "skipped": [],
        "would_overwrite": [],
        "overwritten": [],
        "errors": [],
    }

    effective_mappings = resolve_mappings(profile, bootstrap_root)

    for mapping in effective_mappings:
        source_path = os.path.join(bootstrap_root, mapping["source"])
        dest_path = os.path.join(target_dir, mapping["destination"])

        if not os.path.isfile(source_path):
            results["errors"].append(
                (mapping["destination"], f"source template not found: {mapping['source']}")
            )
            print(f"  [ERROR] {mapping['destination']} — source not found: {mapping['source']}")
            continue

        # Ensure parent directory exists (or note it in dry-run)
        dest_dir = os.path.dirname(dest_path)
        if dest_dir:
            ensure_directory(dest_dir, args.dry_run)

        status = apply_template(
            source_path, dest_path, mapping, ctx,
        )

        dest_label = mapping["destination"]
        if status == "created":
            results["created"].append(dest_label)
            print(f"  [CREATED]  {dest_label}")
        elif status == "skipped":
            results["skipped"].append(dest_label)
            print(f"  [SKIPPED]  {dest_label} (already exists; use --force to overwrite)")
        elif status == "would_overwrite":
            results["would_overwrite"].append(dest_label)
            print(f"  [WOULD OVERWRITE] {dest_label}")
        elif status == "overwritten":
            results["overwritten"].append(dest_label)
            print(f"  [OVERWRITTEN] {dest_label}")
        elif status.startswith("error:"):
            msg = status[len("error:"):]
            results["errors"].append((dest_label, msg))
            print(f"  [ERROR]    {dest_label} — {msg}")

    print()
    print("=== Summary ===")
    print(f"  Created       : {len(results['created'])}")
    print(f"  Skipped       : {len(results['skipped'])}")
    if args.dry_run:
        print(f"  Would overwrite: {len(results['would_overwrite'])}")
    else:
        print(f"  Overwritten   : {len(results['overwritten'])}")
    print(f"  Errors        : {len(results['errors'])}")

    if results["errors"]:
        print()
        print("Errors encountered — review the output above.")
        sys.exit(1)

    if args.dry_run:
        print()
        print("Dry run complete. No files were written.")
        print(
            "Re-run without --dry-run to apply, or add --force to overwrite existing files."
        )
    else:
        print()
        if results["created"] or results["overwritten"]:
            print("Bootstrap scaffold applied successfully.")
            print()
            print("Next steps:")
            print("  1. Run the discovery/bootstrap prompt against the target repo:")
            print("       prompts/new-repo-bootstrap.md  (new repo)")
            print("       prompts/existing-repo-discovery.md  (existing repo)")
            print("  2. The agent will inspect the target repo and fill template placeholders")
            print("     with real, evidence-based content.")
            print("  3. Validate the result:")
            print(f"       python scripts/validate_bootstrap.py --target-dir {target_dir}")
        else:
            print("No files were created (all targets already existed and --force was not set).")
            print(f"  Run with --force to overwrite, or validate the current state:")
            print(f"       python scripts/validate_bootstrap.py --target-dir {target_dir}")

    sys.exit(0)


if __name__ == "__main__":
    main()
