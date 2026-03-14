#!/usr/bin/env python3
"""
suggest_profile.py

Inspects a target repository and suggests the most likely bootstrap profile
based on explicit file-system evidence.  Read-only — never mutates the target.

Usage:
    python scripts/suggest_profile.py --target-dir /path/to/repo
    python scripts/suggest_profile.py --target-dir /path/to/repo --verbose
    python scripts/suggest_profile.py --target-dir /path/to/repo --json

Exit codes:
    0 — suggestion produced (even if confidence is low or profile is generic)
    1 — error (target directory missing, unreadable, etc.)

JSON output schema (--json flag) — stable contract:

    {
      "target_dir":            string  — absolute path of the inspected directory,
      "suggested_profile":     string  — one of: python-service, infra-repo,
                                         vscode-extension, kubernetes-platform, generic,
      "confidence":            string  — one of: high, medium, low,
      "score":                 int     — sum of matched signal weights for the top profile,
      "max_score":             int     — sum of all signal weights for the top profile,
      "matched_signals":       [str]   — human-readable labels for matched signals,
      "alternative_candidates": [      — profiles with score > 0 other than the top:
        {
          "profile":   string,
          "score":     int,
          "confidence": string,
          "matched":   [str]
        }
      ],
      "all_scores":            {str: int} — score for every known profile (always present),
      "recommended_command":   string  — ready-to-run apply_bootstrap.py command
    }

Fields and their names are stable.  Do not rename or remove fields without a
semver minor version bump and a CHANGELOG entry.  New fields may be added
without a version bump, but should be documented here.
"""

import argparse
import json
import os
import sys

# ─────────────────────────────────────────────────────────────────────────────
# Profile signal definitions
#
# Each entry is a dict:
#   signal    — short human-readable label
#   check     — callable(target_dir) -> bool
#   weight    — 1 (standard) or 2 (strong indicator)
# ─────────────────────────────────────────────────────────────────────────────

def _has_file(target_dir, *rel_paths):
    """Return True if any of the given relative paths exist as files."""
    return any(os.path.isfile(os.path.join(target_dir, p)) for p in rel_paths)


def _has_dir(target_dir, *rel_paths):
    """Return True if any of the given relative paths exist as directories."""
    return any(os.path.isdir(os.path.join(target_dir, p)) for p in rel_paths)


def _has_glob_ext(target_dir, extension, max_depth=3):
    """
    Return True if any file with the given extension exists within max_depth
    levels of target_dir.  Uses os.walk to avoid shell execution.
    """
    for root, _dirs, files in os.walk(target_dir):
        depth = root[len(target_dir):].count(os.sep)
        if depth >= max_depth:
            _dirs.clear()
            continue
        for fname in files:
            if fname.endswith(extension):
                return True
    return False


def _has_filename_in_tree(target_dir, filename, max_depth=3):
    """
    Return True if a file with the exact given name exists anywhere within
    max_depth levels of target_dir.
    """
    for root, _dirs, files in os.walk(target_dir):
        depth = root[len(target_dir):].count(os.sep)
        if depth >= max_depth:
            _dirs.clear()
            continue
        if filename in files:
            return True
    return False
    """Return True if rel_path exists and contains substring (case-insensitive)."""
    full = os.path.join(target_dir, rel_path)
    if not os.path.isfile(full):
        return False
    try:
        with open(full, "r", encoding="utf-8", errors="ignore") as f:
            return substring.lower() in f.read().lower()
    except OSError:
        return False


# ── python-service signals ────────────────────────────────────────────────────

PYTHON_SERVICE_SIGNALS = [
    {
        "signal": "pyproject.toml present",
        "check": lambda d: _has_file(d, "pyproject.toml"),
        "weight": 2,
    },
    {
        "signal": "requirements.txt or setup.py present",
        "check": lambda d: _has_file(d, "requirements.txt", "setup.py", "setup.cfg"),
        "weight": 2,
    },
    {
        "signal": "src/ or app/ directory present",
        "check": lambda d: _has_dir(d, "src", "app"),
        "weight": 1,
    },
    {
        "signal": "tests/ directory present",
        "check": lambda d: _has_dir(d, "tests", "test"),
        "weight": 1,
    },
    {
        "signal": ".py files present",
        "check": lambda d: _has_glob_ext(d, ".py"),
        "weight": 1,
    },
    {
        "signal": "conftest.py present (pytest)",
        "check": lambda d: _has_file(d, "conftest.py") or _has_file(d, "tests/conftest.py"),
        "weight": 1,
    },
]

# ── infra-repo signals ────────────────────────────────────────────────────────

INFRA_REPO_SIGNALS = [
    {
        "signal": "Terraform files (.tf) present",
        "check": lambda d: _has_glob_ext(d, ".tf"),
        "weight": 2,
    },
    {
        "signal": "environments/ or modules/ directory present",
        "check": lambda d: _has_dir(d, "environments", "modules", "inventory"),
        "weight": 2,
    },
    {
        "signal": "Ansible playbook or inventory file present",
        "check": lambda d: (
            _has_glob_ext(d, ".yml") and
            any(
                _has_file(d, p)
                for p in ("playbook.yml", "site.yml", "inventory", "ansible.cfg")
            )
        ),
        "weight": 1,
    },
    {
        "signal": "helm/ charts/ directory present",
        "check": lambda d: _has_dir(d, "helm", "charts"),
        "weight": 1,
    },
    {
        "signal": "docs/ present but no clear app runtime",
        "check": lambda d: _has_dir(d, "docs") and not _has_glob_ext(d, ".py") and not _has_file(d, "package.json"),
        "weight": 1,
    },
]

# ── vscode-extension signals ──────────────────────────────────────────────────

VSCODE_EXTENSION_SIGNALS = [
    {
        "signal": "package.json present",
        "check": lambda d: _has_file(d, "package.json"),
        "weight": 1,
    },
    {
        "signal": "package.json contains vscode engine/contributes",
        "check": lambda d: _file_contains(d, "package.json", "vscode"),
        "weight": 2,
    },
    {
        "signal": "extension.ts or extension.js present",
        "check": lambda d: _has_file(d, "src/extension.ts", "src/extension.js", "extension.ts", "extension.js"),
        "weight": 2,
    },
    {
        "signal": ".vscodeignore present",
        "check": lambda d: _has_file(d, ".vscodeignore"),
        "weight": 2,
    },
]

# ── kubernetes-platform signals ───────────────────────────────────────────────

KUBERNETES_PLATFORM_SIGNALS = [
    {
        "signal": "Chart.yaml present",
        "check": lambda d: _has_file(d, "Chart.yaml") or _has_filename_in_tree(d, "Chart.yaml"),
        "weight": 2,
    },
    {
        "signal": "values.yaml present",
        "check": lambda d: _has_file(d, "values.yaml"),
        "weight": 1,
    },
    {
        "signal": "kustomization.yaml present",
        "check": lambda d: _has_file(d, "kustomization.yaml") or _has_filename_in_tree(d, "kustomization.yaml"),
        "weight": 2,
    },
    {
        "signal": "manifests/ or clusters/ directory present",
        "check": lambda d: _has_dir(d, "manifests", "clusters"),
        "weight": 2,
    },
    {
        "signal": "charts/ directory present",
        "check": lambda d: _has_dir(d, "charts"),
        "weight": 1,
    },
]

# ── profile registry ──────────────────────────────────────────────────────────

PROFILES = {
    "python-service": PYTHON_SERVICE_SIGNALS,
    "infra-repo": INFRA_REPO_SIGNALS,
    "vscode-extension": VSCODE_EXTENSION_SIGNALS,
    "kubernetes-platform": KUBERNETES_PLATFORM_SIGNALS,
}

# ─────────────────────────────────────────────────────────────────────────────
# Scoring
# ─────────────────────────────────────────────────────────────────────────────

def score_profile(target_dir, signals):
    """
    Evaluate signals for a profile.

    Returns:
        matched   — list of signal labels that matched
        score     — integer sum of matched signal weights
        max_score — integer sum of all signal weights
    """
    matched = []
    score = 0
    max_score = sum(s["weight"] for s in signals)
    for sig in signals:
        try:
            hit = sig["check"](target_dir)
        except Exception:
            hit = False
        if hit:
            matched.append(sig["signal"])
            score += sig["weight"]
    return matched, score, max_score


def confidence_label(score, max_score):
    """Map a score fraction to a human-readable confidence label."""
    if max_score == 0:
        return "low"
    ratio = score / max_score
    if ratio >= 0.65:
        return "high"
    if ratio >= 0.35:
        return "medium"
    return "low"


def classify(target_dir):
    """
    Score all profiles and return a structured classification result.

    Returns a dict:
        suggested       — profile name (str)
        confidence      — "high" / "medium" / "low"
        score           — int
        max_score       — int
        matched         — list of matched signal labels
        alternatives    — list of (profile_name, score, confidence, matched) for runner-up profiles
        all_scores      — dict of {profile: score}
    """
    results = {}
    for name, signals in PROFILES.items():
        matched, score, max_score = score_profile(target_dir, signals)
        results[name] = {
            "score": score,
            "max_score": max_score,
            "matched": matched,
            "confidence": confidence_label(score, max_score),
        }

    # Sort by score descending
    ranked = sorted(results.items(), key=lambda x: x[1]["score"], reverse=True)

    top_name, top_data = ranked[0]

    # If the top score is zero, fall back to generic
    if top_data["score"] == 0:
        return {
            "suggested": "generic",
            "confidence": "low",
            "score": 0,
            "max_score": top_data["max_score"],
            "matched": [],
            "alternatives": [],
            "all_scores": {n: d["score"] for n, d in ranked},
        }

    alternatives = []
    for name, data in ranked[1:]:
        if data["score"] > 0:
            alternatives.append({
                "profile": name,
                "score": data["score"],
                "confidence": data["confidence"],
                "matched": data["matched"],
            })

    return {
        "suggested": top_name,
        "confidence": top_data["confidence"],
        "score": top_data["score"],
        "max_score": top_data["max_score"],
        "matched": top_data["matched"],
        "alternatives": alternatives,
        "all_scores": {n: d["score"] for n, d in ranked},
    }


# ─────────────────────────────────────────────────────────────────────────────
# Output formatting
# ─────────────────────────────────────────────────────────────────────────────

def print_report(target_dir, result, verbose=False):
    """Print a human-readable profile suggestion report."""
    print(f"Profile suggestion report")
    print(f"  Target directory : {target_dir}")
    print()
    print(f"  Suggested profile : {result['suggested']}")
    print(f"  Confidence        : {result['confidence']}")
    print()

    if result["matched"]:
        print("  Matching signals:")
        for sig in result["matched"]:
            print(f"    + {sig}")
    else:
        print("  Matching signals  : (none — weak or absent evidence)")
    print()

    if result["alternatives"]:
        print("  Alternative candidates:")
        for alt in result["alternatives"]:
            print(f"    {alt['profile']}  (score {alt['score']}, confidence {alt['confidence']})")
            if verbose and alt["matched"]:
                for sig in alt["matched"]:
                    print(f"      + {sig}")
        print()

    if verbose and not result["alternatives"]:
        print("  All profile scores:")
        for name, score in result["all_scores"].items():
            print(f"    {name:<25} {score}")
        print()

    if result["suggested"] == "generic":
        print("  Note: Evidence was absent or too weak to suggest a specific profile.")
        print("        'generic' is the safe fallback for unknown or mixed repos.")
        print()

    # Recommended next command
    profile_flag = (
        f" --profile {result['suggested']}"
        if result["suggested"] != "generic"
        else ""
    )
    print("  Recommended next command:")
    print(f"    python scripts/apply_bootstrap.py --target-dir {target_dir} --dry-run{profile_flag}")
    print()
    print("  Note: Profile selection is the maintainer's decision.")
    print("        This report is advisory only — it does not apply anything.")
    print()


def print_json_report(target_dir, result):
    """Print a JSON profile suggestion report."""
    output = {
        "target_dir": target_dir,
        "suggested_profile": result["suggested"],
        "confidence": result["confidence"],
        "score": result["score"],
        "max_score": result["max_score"],
        "matched_signals": result["matched"],
        "alternative_candidates": result["alternatives"],
        "all_scores": result["all_scores"],
        "recommended_command": (
            f"python scripts/apply_bootstrap.py --target-dir {target_dir} --dry-run"
            + (f" --profile {result['suggested']}" if result["suggested"] != "generic" else "")
        ),
    }
    print(json.dumps(output, indent=2))


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Inspect a target repository and suggest the most likely bootstrap profile. "
            "Read-only — never modifies the target repository."
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
        help="Show additional signal detail and all profile scores.",
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
        print(f"ERROR: target directory not found or not a directory: {target_dir}",
              file=sys.stderr)
        sys.exit(1)

    result = classify(target_dir)

    if args.json_output:
        print_json_report(target_dir, result)
    else:
        print_report(target_dir, result, verbose=args.verbose)


if __name__ == "__main__":
    main()
