#!/usr/bin/env python3
"""
bootstrap_doctor.py

Read-only diagnostic tool that inspects a target repository and reports its
bootstrap health, drift, and recommended next action.

Usage:
    python scripts/bootstrap_doctor.py --target-dir /path/to/repo
    python scripts/bootstrap_doctor.py --target-dir /path/to/repo --verbose
    python scripts/bootstrap_doctor.py --target-dir /path/to/repo --json

Exit codes:
    0 — report produced successfully (even if health is poor)
    1 — operational error (target directory missing, unreadable, etc.)

Health states (stable names — do not rename without a version bump):
    unbootstrapped                    — no marker, minimal bootstrap evidence
    scaffold-applied-unpopulated      — marker present, placeholders widespread
    partially-populated               — marker present, some populated, some placeholders remain
    populated-and-healthy             — marker present, required files present, no placeholder issues
    stale-version-review-recommended  — target version materially behind current source
    profile-mismatch-review-recommended — marker profile differs from suggested with meaningful evidence

Marker era values (aligned with bootstrap_status.py semantics):
    pre-version  — no version recorded, or version is still a placeholder
    pre-profile  — version is semver but profile not recorded or still a placeholder
    versioned    — both version (semver) and profile are recorded
    unknown      — version field is present but not a recognizable semver value

This tool is advisory and read-only. It never creates, modifies, or deletes files.
"""

import argparse
import json
import os
import re
import sys

# ─────────────────────────────────────────────────────────────────────────────
# Constants — aligned with validate_bootstrap.py expectations
# ─────────────────────────────────────────────────────────────────────────────

# Required files in a bootstrapped target repository.
# Keep in sync with TARGET_REPO_REQUIRED_FILES in validate_bootstrap.py.
TARGET_REQUIRED_FILES = [
    "AGENTS.md",
    "IMPLEMENTATION_TRACKER.md",
    "docs/ai/REPO_MAP.md",
    "docs/ai/SOURCE_REFRESH.md",
    "docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md",
    "bootstrap/BOOTSTRAP_SOURCE.md",
    "artifacts/ai/repo_discovery.json",
]

# Files checked for unfilled placeholder markers.
# Keep in sync with TARGET_REPO_PLACEHOLDER_FILES in validate_bootstrap.py.
TARGET_PLACEHOLDER_FILES = [
    "AGENTS.md",
    "IMPLEMENTATION_TRACKER.md",
    "docs/ai/REPO_MAP.md",
    "docs/ai/SOURCE_REFRESH.md",
    "docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md",
    "bootstrap/BOOTSTRAP_SOURCE.md",
]

PLACEHOLDER_RE = re.compile(r"\{\{[A-Z_][A-Z0-9_]*\}\}")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+")

# ─────────────────────────────────────────────────────────────────────────────
# Marker parsing — aligned with bootstrap_status.py
# ─────────────────────────────────────────────────────────────────────────────

def parse_marker(target_dir):
    """
    Parse bootstrap/BOOTSTRAP_SOURCE.md in the target repo.

    Returns a dict with marker fields; values may be None (not recorded) or
    the raw placeholder string if never filled.
    """
    marker_path = os.path.join(target_dir, "bootstrap", "BOOTSTRAP_SOURCE.md")
    result = {
        "found": False,
        "path": marker_path,
        "source_repo": None,
        "version": None,
        "revision": None,
        "date": None,
        "agent": None,
        "prompt": None,
        "profile": None,
    }

    if not os.path.isfile(marker_path):
        return result

    result["found"] = True

    field_map = {
        "bootstrap source repository": "source_repo",
        "bootstrap source version": "version",
        "bootstrap source revision": "revision",
        "bootstrap date": "date",
        "agent / operator": "agent",
        "prompt used": "prompt",
        "bootstrap profile": "profile",
    }

    try:
        with open(marker_path, "r", encoding="utf-8") as f:
            for line in f:
                if "|" not in line:
                    continue
                parts = [p.strip() for p in line.strip().strip("|").split("|")]
                if len(parts) < 2:
                    continue
                key = parts[0].lower()
                value = parts[1] if len(parts) > 1 else ""
                if key in field_map:
                    result[field_map[key]] = value or None
    except OSError:
        pass

    return result


def is_placeholder(value):
    """Return True if the value looks like an unfilled {{PLACEHOLDER}}."""
    if value is None:
        return False
    return bool(re.match(r"^\{\{[A-Z_][A-Z0-9_]*\}\}$", value.strip()))


# ─────────────────────────────────────────────────────────────────────────────
# File presence checks
# ─────────────────────────────────────────────────────────────────────────────

def check_required_files(target_dir):
    """
    Check required managed files in the target repo.

    Returns:
        present  — list of rel_paths that exist
        missing  — list of rel_paths that are absent
    """
    present = []
    missing = []
    for rel_path in TARGET_REQUIRED_FILES:
        if os.path.isfile(os.path.join(target_dir, rel_path)):
            present.append(rel_path)
        else:
            missing.append(rel_path)
    return present, missing


# ─────────────────────────────────────────────────────────────────────────────
# Placeholder checks
# ─────────────────────────────────────────────────────────────────────────────

def check_placeholders(target_dir):
    """
    Count unfilled {{PLACEHOLDER}} markers across managed placeholder files.

    Returns:
        files_with_placeholders — list of rel_paths that still contain markers
        files_clean             — list of present rel_paths with no markers
        total_count             — total number of placeholder instances found
    """
    files_with = []
    files_clean = []
    total = 0
    for rel_path in TARGET_PLACEHOLDER_FILES:
        full = os.path.join(target_dir, rel_path)
        if not os.path.isfile(full):
            continue
        try:
            with open(full, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue
        found = PLACEHOLDER_RE.findall(content)
        if found:
            files_with.append(rel_path)
            total += len(found)
        else:
            files_clean.append(rel_path)
    return files_with, files_clean, total


# ─────────────────────────────────────────────────────────────────────────────
# Profile suggestion — inline, aligned with suggest_profile.py heuristics
# ─────────────────────────────────────────────────────────────────────────────

def _has_file(target_dir, *rel_paths):
    return any(os.path.isfile(os.path.join(target_dir, p)) for p in rel_paths)


def _has_dir(target_dir, *rel_paths):
    return any(os.path.isdir(os.path.join(target_dir, p)) for p in rel_paths)


def _has_ext(target_dir, extension, max_depth=3):
    for root, _dirs, files in os.walk(target_dir):
        depth = root[len(target_dir):].count(os.sep)
        if depth >= max_depth:
            _dirs.clear()
            continue
        for fname in files:
            if fname.endswith(extension):
                return True
    return False


def _has_named_file(target_dir, filename, max_depth=3):
    for root, _dirs, files in os.walk(target_dir):
        depth = root[len(target_dir):].count(os.sep)
        if depth >= max_depth:
            _dirs.clear()
            continue
        if filename in files:
            return True
    return False


def _file_contains(target_dir, rel_path, substring):
    full = os.path.join(target_dir, rel_path)
    if not os.path.isfile(full):
        return False
    try:
        with open(full, "r", encoding="utf-8", errors="ignore") as f:
            return substring.lower() in f.read().lower()
    except OSError:
        return False


def _score_python_service(d):
    score = 0
    if _has_file(d, "pyproject.toml"):
        score += 2
    if _has_file(d, "requirements.txt", "setup.py", "setup.cfg"):
        score += 2
    if _has_dir(d, "src", "app"):
        score += 1
    if _has_dir(d, "tests", "test"):
        score += 1
    if _has_ext(d, ".py"):
        score += 1
    return score


def _score_infra_repo(d):
    score = 0
    if _has_ext(d, ".tf"):
        score += 2
    if _has_dir(d, "environments", "modules", "inventory"):
        score += 2
    if _has_dir(d, "helm", "charts"):
        score += 1
    if _has_dir(d, "docs") and not _has_ext(d, ".py") and not _has_file(d, "package.json"):
        score += 1
    return score


def _score_vscode_extension(d):
    score = 0
    if _has_file(d, "package.json"):
        score += 1
    if _file_contains(d, "package.json", "vscode"):
        score += 2
    if _has_file(d, "src/extension.ts", "src/extension.js", "extension.ts", "extension.js"):
        score += 2
    if _has_file(d, ".vscodeignore"):
        score += 2
    return score


def _score_kubernetes_platform(d):
    score = 0
    if _has_file(d, "Chart.yaml") or _has_named_file(d, "Chart.yaml"):
        score += 2
    if _has_file(d, "values.yaml"):
        score += 1
    if _has_file(d, "kustomization.yaml") or _has_named_file(d, "kustomization.yaml"):
        score += 2
    if _has_dir(d, "manifests", "clusters"):
        score += 2
    if _has_dir(d, "charts"):
        score += 1
    return score


def suggest_profile(target_dir):
    """
    Return the suggested profile name and confidence for target_dir.

    Returns:
        (profile_name, confidence, score)
        where confidence is "high", "medium", or "low"
        and profile_name is one of the known profiles or "generic".
    """
    scores = {
        "python-service": _score_python_service(target_dir),
        "infra-repo": _score_infra_repo(target_dir),
        "vscode-extension": _score_vscode_extension(target_dir),
        "kubernetes-platform": _score_kubernetes_platform(target_dir),
    }
    max_score = max(scores.values())
    if max_score == 0:
        return "generic", "low", 0

    top = max(scores, key=lambda k: scores[k])
    score = scores[top]

    # Max possible scores for each profile (sum of weights)
    max_possible = {
        "python-service": 8,
        "infra-repo": 6,
        "vscode-extension": 7,
        "kubernetes-platform": 8,
    }
    ratio = score / max_possible.get(top, score)
    if ratio >= 0.65:
        confidence = "high"
    elif ratio >= 0.35:
        confidence = "medium"
    else:
        confidence = "low"

    return top, confidence, score


# ─────────────────────────────────────────────────────────────────────────────
# Version comparison helper
# ─────────────────────────────────────────────────────────────────────────────

def _read_source_version(bootstrap_root):
    """Read the VERSION file from the bootstrap source repo."""
    path = os.path.join(bootstrap_root, "VERSION")
    if not os.path.isfile(path):
        return None
    try:
        return open(path, "r", encoding="utf-8").read().strip()
    except OSError:
        return None


def _semver_tuple(version_str):
    """Parse a semver string to a tuple of ints, or None on failure."""
    if version_str is None:
        return None
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", version_str)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _is_materially_behind(target_version, source_version):
    """
    Return True if the target version is materially behind the source version.
    Considers minor or major version differences as material.
    """
    tv = _semver_tuple(target_version)
    sv = _semver_tuple(source_version)
    if tv is None or sv is None:
        return False
    # Any major or minor difference is material
    return sv[0] > tv[0] or (sv[0] == tv[0] and sv[1] > tv[1])


# ─────────────────────────────────────────────────────────────────────────────
# Marker era classification
# ─────────────────────────────────────────────────────────────────────────────

def classify_era(marker):
    """
    Classify the marker era based on recorded version and profile fields.

    Returns one of: "pre-version", "pre-profile", "versioned", "unknown"

    Semantics are aligned with bootstrap_status.py's era interpretation:
      pre-version — version is absent, a placeholder, or not a semver string
      pre-profile  — version is valid semver but profile is absent or placeholder
      versioned    — version is valid semver and profile is recorded
      unknown      — version field is present but not a recognizable semver value
    """
    version = marker.get("version")
    profile = marker.get("profile")

    if version is None or is_placeholder(version):
        return "pre-version"
    if not SEMVER_RE.match(version):
        # Version field present but not parseable semver — mirrors bootstrap_status.py "unknown" era
        return "unknown"

    if profile is None or is_placeholder(profile):
        return "pre-profile"

    return "versioned"


# ─────────────────────────────────────────────────────────────────────────────
# Health classification
# ─────────────────────────────────────────────────────────────────────────────

def classify_health(target_dir, marker, present_files, missing_files,
                    files_with_placeholders, files_clean, total_placeholders,
                    suggested_profile, profile_confidence,
                    source_version):
    """
    Classify the overall health of a target repo given all collected signals.

    Returns a health state string (one of the stable state names).
    """
    total_required = len(TARGET_REQUIRED_FILES)
    present_count = len(present_files)
    placeholder_file_count = len(TARGET_PLACEHOLDER_FILES)
    checked_count = len(files_with_placeholders) + len(files_clean)

    # 1. No marker at all → unbootstrapped
    if not marker["found"]:
        return "unbootstrapped"

    # 2. Marker found, but most/all placeholder files still have markers → scaffold applied only
    if checked_count > 0 and len(files_with_placeholders) == checked_count:
        return "scaffold-applied-unpopulated"

    # 3. Some files have placeholders, some are clean → partially populated
    if files_with_placeholders:
        return "partially-populated"

    # At this point: marker found, no placeholders remaining in checked files.
    # Check for required file gaps.
    if missing_files:
        return "partially-populated"

    # 4. All required files present, no placeholders → check for stale version
    recorded_version = marker.get("version")
    if (not is_placeholder(recorded_version) and recorded_version and
            source_version and _is_materially_behind(recorded_version, source_version)):
        return "stale-version-review-recommended"

    # 5. Check for profile mismatch (only when suggestion is confident)
    recorded_profile = marker.get("profile")
    if (recorded_profile and not is_placeholder(recorded_profile) and
            suggested_profile != "generic" and
            profile_confidence in ("high", "medium") and
            suggested_profile != recorded_profile):
        return "profile-mismatch-review-recommended"

    # 6. Everything looks good
    return "populated-and-healthy"


# ─────────────────────────────────────────────────────────────────────────────
# Next-action recommendations
# ─────────────────────────────────────────────────────────────────────────────

def recommend_actions(health_state, target_dir, marker, missing_files,
                      suggested_profile, source_version):
    """
    Return a list of recommended next command strings for the operator.

    Commands are conservative — no --force flags recommended by default.
    """
    cmds = []
    td = target_dir

    if health_state == "unbootstrapped":
        # Suggest profile first, then apply
        cmds.append(f"python scripts/suggest_profile.py --target-dir {td}")
        profile_flag = (
            f" --profile {suggested_profile}"
            if suggested_profile != "generic"
            else ""
        )
        cmds.append(
            f"python scripts/apply_bootstrap.py --target-dir {td} --dry-run{profile_flag}"
        )

    elif health_state == "scaffold-applied-unpopulated":
        cmds.append(f"python scripts/validate_bootstrap.py --target-dir {td}")
        cmds.append(
            "# Then run the bootstrap prompt against the target repo to fill placeholders"
        )

    elif health_state == "partially-populated":
        cmds.append(f"python scripts/validate_bootstrap.py --target-dir {td}")
        cmds.append(
            "# Review unfilled placeholders above and complete population of managed files"
        )

    elif health_state == "populated-and-healthy":
        cmds.append(f"python scripts/validate_bootstrap.py --target-dir {td}")
        cmds.append(f"python scripts/bootstrap_status.py --target-dir {td}")

    elif health_state == "stale-version-review-recommended":
        cmds.append(f"python scripts/refresh_bootstrap.py --target-dir {td} --dry-run")
        cmds.append(f"python scripts/validate_bootstrap.py --target-dir {td}")

    elif health_state == "profile-mismatch-review-recommended":
        cmds.append(f"python scripts/suggest_profile.py --target-dir {td} --verbose")
        cmds.append(f"python scripts/bootstrap_status.py --target-dir {td}")
        cmds.append(
            "# If profile mismatch is confirmed, consider re-applying with the correct profile"
        )

    return cmds


# ─────────────────────────────────────────────────────────────────────────────
# Profile alignment
# ─────────────────────────────────────────────────────────────────────────────

def profile_alignment(recorded_profile, suggested_profile, profile_confidence):
    """
    Classify alignment between the recorded marker profile and the current suggestion.

    Returns one of: "aligned", "mismatch", "insufficient-evidence", "not-recorded"
    """
    if not recorded_profile or is_placeholder(recorded_profile):
        return "not-recorded"
    if profile_confidence == "low" or suggested_profile == "generic":
        return "insufficient-evidence"
    if recorded_profile == suggested_profile:
        return "aligned"
    return "mismatch"


# ─────────────────────────────────────────────────────────────────────────────
# Marker status summary
# ─────────────────────────────────────────────────────────────────────────────

def marker_status(marker):
    """
    Return a brief status string for the marker.

    Returns one of: "missing", "present", "incomplete"
    """
    if not marker["found"]:
        return "missing"

    # Check if any core fields are None or placeholders
    core_fields = ["source_repo", "version", "date"]
    for field in core_fields:
        v = marker.get(field)
        if v is None or is_placeholder(v):
            return "incomplete"
    return "present"


# ─────────────────────────────────────────────────────────────────────────────
# Required files status summary
# ─────────────────────────────────────────────────────────────────────────────

def required_files_status(present_files, missing_files):
    """
    Return a brief status string for required file presence.

    Returns one of: "all-present", "minor-gaps", "major-gaps"
    """
    total = len(TARGET_REQUIRED_FILES)
    present = len(present_files)
    missing = len(missing_files)

    if missing == 0:
        return "all-present"
    if missing <= 2:
        return "minor-gaps"
    return "major-gaps"


# ─────────────────────────────────────────────────────────────────────────────
# Placeholder status summary
# ─────────────────────────────────────────────────────────────────────────────

def placeholder_status(files_with, files_clean, total_count):
    """
    Return a brief status string for placeholder presence.

    Returns one of: "placeholders-remain", "no-placeholders-detected", "mixed"
    """
    checked = len(files_with) + len(files_clean)
    if checked == 0:
        return "no-placeholders-detected"
    if not files_with:
        return "no-placeholders-detected"
    if not files_clean:
        return "placeholders-remain"
    return "mixed"


# ─────────────────────────────────────────────────────────────────────────────
# Collect all signals
# ─────────────────────────────────────────────────────────────────────────────

def audit(target_dir, bootstrap_root):
    """
    Collect all diagnostic signals for a target repo.

    Returns a structured result dict.
    """
    marker = parse_marker(target_dir)
    present_files, missing_files = check_required_files(target_dir)
    files_with_ph, files_clean, total_ph = check_placeholders(target_dir)

    suggested_prof, prof_confidence, prof_score = suggest_profile(target_dir)
    source_ver = _read_source_version(bootstrap_root)

    era = classify_era(marker) if marker["found"] else "pre-version"
    m_status = marker_status(marker)
    rf_status = required_files_status(present_files, missing_files)
    ph_status = placeholder_status(files_with_ph, files_clean, total_ph)
    p_alignment = profile_alignment(
        marker.get("profile"), suggested_prof, prof_confidence
    )

    recorded_profile = marker.get("profile")
    if is_placeholder(recorded_profile):
        recorded_profile = None

    recorded_version = marker.get("version")
    if is_placeholder(recorded_version):
        recorded_version = None

    health = classify_health(
        target_dir, marker, present_files, missing_files,
        files_with_ph, files_clean, total_ph,
        suggested_prof, prof_confidence,
        source_ver,
    )

    recommendations = recommend_actions(
        health, target_dir, marker, missing_files,
        suggested_prof, source_ver,
    )

    return {
        "target_dir": target_dir,
        "bootstrapped": marker["found"],
        "marker_status": m_status,
        "marker_era": era,
        "recorded_version": recorded_version,
        "source_version": source_ver,
        "recorded_profile": recorded_profile,
        "suggested_profile": suggested_prof,
        "profile_confidence": prof_confidence,
        "profile_alignment": p_alignment,
        "required_files_status": rf_status,
        "present_files": present_files,
        "missing_files": missing_files,
        "placeholder_status": ph_status,
        "files_with_placeholders": files_with_ph,
        "files_clean": files_clean,
        "total_placeholder_count": total_ph,
        "health_state": health,
        "recommendations": recommendations,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Human-readable output
# ─────────────────────────────────────────────────────────────────────────────

# Human-readable labels for each health state
HEALTH_LABELS = {
    "unbootstrapped":                   "Unbootstrapped",
    "scaffold-applied-unpopulated":     "Scaffold applied — not yet populated",
    "partially-populated":              "Partially populated",
    "populated-and-healthy":            "Populated and healthy",
    "stale-version-review-recommended": "Stale version — review recommended",
    "profile-mismatch-review-recommended": "Profile mismatch — review recommended",
}

HEALTH_DESCRIPTIONS = {
    "unbootstrapped": (
        "No bootstrap marker found. The repo does not appear to have been bootstrapped, "
        "or the marker was removed."
    ),
    "scaffold-applied-unpopulated": (
        "Bootstrap marker is present and the scaffold was applied, but placeholder "
        "markers still fill all managed files. The repo has not been populated yet."
    ),
    "partially-populated": (
        "Some managed files have been populated with real content, but others still "
        "contain unfilled {{PLACEHOLDER}} markers or are missing."
    ),
    "populated-and-healthy": (
        "Bootstrap marker is present, all required files exist, and no unfilled "
        "placeholder markers were detected. The repo appears fully bootstrapped."
    ),
    "stale-version-review-recommended": (
        "The recorded bootstrap version is materially behind the current source version. "
        "Consider running a refresh to pick up updated templates."
    ),
    "profile-mismatch-review-recommended": (
        "The recorded bootstrap profile differs from the currently suggested profile "
        "with meaningful evidence. Review whether re-applying with the correct profile "
        "would improve the scaffold."
    ),
}


def print_report(result, verbose=False):
    """Print a human-readable doctor report."""
    print("Bootstrap Doctor Report")
    print(f"  Target directory  : {result['target_dir']}")
    print()

    # Bootstrapped status
    bootstrapped_str = "yes" if result["bootstrapped"] else "no"
    print(f"  Bootstrapped      : {bootstrapped_str}")
    print(f"  Marker status     : {result['marker_status']}")
    if result["bootstrapped"]:
        print(f"  Marker era        : {result['marker_era']}")
    print()

    # Version and profile
    rv = result["recorded_version"] or "(not recorded)"
    sv = result["source_version"] or "(unknown)"
    rp = result["recorded_profile"] or "(not recorded)"
    sp = result["suggested_profile"]

    print(f"  Recorded version  : {rv}")
    print(f"  Source version    : {sv}")
    print(f"  Recorded profile  : {rp}")
    print(f"  Suggested profile : {sp}  (confidence: {result['profile_confidence']})")
    print(f"  Profile alignment : {result['profile_alignment']}")
    print()

    # Required files
    rf = result["required_files_status"]
    print(f"  Required files    : {rf}")
    if verbose and result["missing_files"]:
        for f in result["missing_files"]:
            print(f"    [MISSING] {f}")
    elif result["missing_files"] and not verbose:
        print(f"    ({len(result['missing_files'])} missing — use --verbose to list)")
    print()

    # Placeholder status
    ph = result["placeholder_status"]
    print(f"  Placeholder status: {ph}")
    if verbose and result["files_with_placeholders"]:
        for f in result["files_with_placeholders"]:
            print(f"    [HAS PLACEHOLDERS] {f}")
    elif result["files_with_placeholders"] and not verbose:
        print(
            f"    ({len(result['files_with_placeholders'])} file(s) with placeholders — "
            f"use --verbose to list)"
        )
    print()

    # Health classification
    health = result["health_state"]
    label = HEALTH_LABELS.get(health, health)
    description = HEALTH_DESCRIPTIONS.get(health, "")
    print(f"  Health state      : {health}")
    print(f"    → {label}")
    if description:
        print(f"    {description}")
    print()

    # Recommendations
    if result["recommendations"]:
        print("  Recommended next action(s):")
        for cmd in result["recommendations"]:
            if cmd.startswith("#"):
                print(f"    {cmd}")
            else:
                print(f"    {cmd}")
    else:
        print("  No further action needed.")
    print()

    print("  Note: This report is advisory only. The doctor never modifies any files.")
    print()


def print_json_report(result):
    """Print a JSON doctor report."""
    output = {
        "target_dir": result["target_dir"],
        "bootstrapped": result["bootstrapped"],
        "marker_status": result["marker_status"],
        "marker_era": result["marker_era"],
        "recorded_version": result["recorded_version"],
        "source_version": result["source_version"],
        "recorded_profile": result["recorded_profile"],
        "suggested_profile": result["suggested_profile"],
        "profile_confidence": result["profile_confidence"],
        "profile_alignment": result["profile_alignment"],
        "required_files_status": result["required_files_status"],
        "missing_files": result["missing_files"],
        "placeholder_status": result["placeholder_status"],
        "files_with_placeholders": result["files_with_placeholders"],
        "total_placeholder_count": result["total_placeholder_count"],
        "health_state": result["health_state"],
        "recommendations": result["recommendations"],
    }
    print(json.dumps(output, indent=2))


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def find_bootstrap_root(script_path):
    """Derive bootstrap repo root from this script's location (scripts/ -> parent)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(script_path)))


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Inspect a target repository and report its bootstrap health, drift, "
            "and recommended next action. Read-only — never modifies any files."
        )
    )
    parser.add_argument(
        "--target-dir",
        required=True,
        help="Path to the target repository to inspect.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show additional detail (missing files, files with placeholders).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output result as JSON instead of human-readable text.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    target_dir = os.path.abspath(args.target_dir)
    if not os.path.isdir(target_dir):
        print(
            f"ERROR: target directory not found or not a directory: {target_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    bootstrap_root = find_bootstrap_root(sys.argv[0])
    result = audit(target_dir, bootstrap_root)

    if args.json_output:
        print_json_report(result)
    else:
        print_report(result, verbose=args.verbose)


if __name__ == "__main__":
    main()
