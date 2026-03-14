#!/usr/bin/env python3
"""
bootstrap_core.py

Small shared internal module for the agent-bootstrap system.

This module centralises the semantic helpers that would otherwise be duplicated
across apply_bootstrap.py, refresh_bootstrap.py, bootstrap_status.py,
bootstrap_doctor.py, validate_bootstrap.py, and run_fixture_selftest.py.

Rules for this module:
- stdlib only, no external dependencies
- small and readable; no clever abstractions
- functions are independent helpers, not a framework
- user-facing CLI/output behaviour stays in each individual script
- when a shared semantic changes, change it here and here only

Public helpers (stable contract — do not rename without updating all callers):
    PLACEHOLDER_RE          — compiled regex matching {{PLACEHOLDER}} tokens
    SEMVER_RE               — compiled regex matching semver strings
    read_version(root)      — read VERSION file; returns (version_str, error_msg)
    load_manifest(root)     — load bootstrap-manifest.yaml; returns raw text or None
    get_supported_profiles() — ordered list of known profile names
    resolve_profile(name)   — validated profile name or raises ValueError
    get_bootstrap_marker_path(target_dir) — absolute path to the marker file
    parse_bootstrap_marker(target_dir)    — parse marker fields; returns dict
    classify_marker_era(marker)           — 'pre-version'|'pre-profile'|'versioned'|'unknown'
    is_placeholder(value)                 — True if value is an unfilled {{TOKEN}}
    has_placeholders(text)                — True if text contains any {{TOKEN}}
    find_placeholders(text)               — list of {{TOKEN}} strings found in text
    resolve_template_mappings(profile)    — effective template mappings for a profile
"""

import os
import re

# ─────────────────────────────────────────────────────────────────────────────
# Compiled regular expressions — shared across all scripts
# ─────────────────────────────────────────────────────────────────────────────

PLACEHOLDER_RE = re.compile(r"\{\{[A-Z_][A-Z0-9_]*\}\}")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+")

# ─────────────────────────────────────────────────────────────────────────────
# Canonical profile definitions
#
# Each entry defines:
#   description       — human-readable summary of the profile
#   template_overrides — mapping from destination path → source template path
#                        (paths relative to the bootstrap repo root)
#
# Generic uses all common templates with no overrides.
# Other profiles override specific templates where family-specific guidance
# materially improves usefulness.
#
# This is the single authoritative definition consumed by apply_bootstrap.py
# and refresh_bootstrap.py.  suggest_profile.py keeps its own signal
# definitions because those are heuristic, not structural.
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
# Canonical common template mappings (profile-independent base)
#
# Used by apply_bootstrap.py and refresh_bootstrap.py via resolve_template_mappings().
# Source paths are relative to the bootstrap repo root.
# ─────────────────────────────────────────────────────────────────────────────

_COMMON_TEMPLATE_MAPPINGS = [
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

# ─────────────────────────────────────────────────────────────────────────────
# Version helpers
# ─────────────────────────────────────────────────────────────────────────────


def read_version(root):
    """
    Read the VERSION file from the bootstrap source repo root.

    Returns:
        (version_str, None)        — successfully read semver string
        (version_str, error_msg)   — read but does not look like semver
        (None, error_msg)          — could not read
    """
    path = os.path.join(root, "VERSION")
    if not os.path.isfile(path):
        return None, "VERSION file not found"
    try:
        with open(path, "r", encoding="utf-8") as f:
            version = f.read().strip()
    except OSError as exc:
        return None, f"cannot read VERSION: {exc}"
    if not SEMVER_RE.match(version):
        return version, f"VERSION does not look like semver: {version!r}"
    return version, None


# ─────────────────────────────────────────────────────────────────────────────
# Manifest helpers
# ─────────────────────────────────────────────────────────────────────────────


def load_manifest(root):
    """
    Load bootstrap-manifest.yaml as raw text.

    Returns the file contents as a string, or None if the file is unreadable.
    """
    path = os.path.join(root, "bootstrap-manifest.yaml")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Profile helpers
# ─────────────────────────────────────────────────────────────────────────────


def get_supported_profiles():
    """Return a sorted list of supported profile names."""
    return sorted(PROFILES.keys())


def resolve_profile(name):
    """
    Validate and return the profile name.

    Returns the profile name unchanged if it is supported.
    Raises ValueError if the name is not recognised.
    """
    if name not in PROFILES:
        raise ValueError(
            f"Unknown profile '{name}'. "
            f"Supported profiles: {', '.join(get_supported_profiles())}"
        )
    return name


# ─────────────────────────────────────────────────────────────────────────────
# Template mapping resolution
# ─────────────────────────────────────────────────────────────────────────────


def resolve_template_mappings(profile_name):
    """
    Return the effective template mappings for the given profile.

    Starts from the common base mappings and applies profile-specific source
    overrides, replacing the template source path for overridden destinations.

    Raises ValueError for an unknown profile name.
    """
    resolve_profile(profile_name)  # validates
    overrides = PROFILES[profile_name]["template_overrides"]
    resolved = []
    for mapping in _COMMON_TEMPLATE_MAPPINGS:
        dest = mapping["destination"]
        if dest in overrides:
            resolved.append({**mapping, "source": overrides[dest]})
        else:
            resolved.append(mapping)
    return resolved


# ─────────────────────────────────────────────────────────────────────────────
# Marker helpers
# ─────────────────────────────────────────────────────────────────────────────

_MARKER_FIELD_MAP = {
    "bootstrap source repository": "source_repo",
    "bootstrap source version": "version",
    "bootstrap source revision": "revision",
    "bootstrap date": "date",
    "agent / operator": "agent",
    "prompt used": "prompt",
    "bootstrap profile": "profile",
}


def get_bootstrap_marker_path(target_dir):
    """Return the absolute path to the bootstrap marker file in a target repo."""
    return os.path.join(target_dir, "bootstrap", "BOOTSTRAP_SOURCE.md")


def parse_bootstrap_marker(target_dir):
    """
    Parse bootstrap/BOOTSTRAP_SOURCE.md in the target repo.

    Returns a dict:
        found      — bool, True if the marker file exists
        path       — absolute path to the marker file
        source_repo, version, revision, date, agent, prompt, profile
                   — field values (str) or None if absent/blank

    Field values may be raw placeholder strings ({{...}}) if never filled.
    """
    marker_path = get_bootstrap_marker_path(target_dir)
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
                if key in _MARKER_FIELD_MAP:
                    result[_MARKER_FIELD_MAP[key]] = value or None
    except OSError:
        pass

    return result


def classify_marker_era(marker):
    """
    Classify the marker era based on recorded version and profile fields.

    Returns one of:
        "pre-version"  — version absent, a placeholder, or not a semver string
        "pre-profile"  — version is valid semver but profile absent or placeholder
        "versioned"    — version is valid semver and profile is recorded
        "unknown"      — version field present but not a recognisable semver value
    """
    version = marker.get("version")
    profile = marker.get("profile")

    if version is None or is_placeholder(version):
        return "pre-version"
    if not SEMVER_RE.match(version):
        return "unknown"
    if profile is None or is_placeholder(profile):
        return "pre-profile"
    return "versioned"


# ─────────────────────────────────────────────────────────────────────────────
# Placeholder helpers
# ─────────────────────────────────────────────────────────────────────────────


def is_placeholder(value):
    """
    Return True if the value is an unfilled {{PLACEHOLDER}} token.

    Matches exactly one token (no surrounding text).  None returns False.
    """
    if value is None:
        return False
    return bool(re.match(r"^\{\{[A-Z_][A-Z0-9_]*\}\}$", value.strip()))


def has_placeholders(text):
    """Return True if the text contains at least one {{PLACEHOLDER}} token."""
    return bool(PLACEHOLDER_RE.search(text))


def find_placeholders(text):
    """Return a list of all {{PLACEHOLDER}} tokens found in the text."""
    return PLACEHOLDER_RE.findall(text)
