"""
Contract tests for bootstrap_doctor.py

These tests prove that the key target-repo diagnostic semantics in
bootstrap_doctor.py remain stable and aligned.  They are intentionally
small and explicit.

Run with:
    python -m unittest discover -s tests -p 'test_*.py'
or:
    python -m unittest tests/test_bootstrap_doctor.py
"""

import json
import os
import sys
import tempfile
import unittest

# Ensure the scripts directory is on the path
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS_DIR = os.path.join(_REPO_ROOT, "scripts")
sys.path.insert(0, _SCRIPTS_DIR)

import bootstrap_doctor as bd
import bootstrap_core as bc


# ─────────────────────────────────────────────────────────────────────────────
# Helpers shared across test classes
# ─────────────────────────────────────────────────────────────────────────────

def _make_marker(version=None, profile=None, found=True,
                 source_repo="https://github.com/example/bootstrap",
                 date="2026-01-01", agent="apply_bootstrap.py",
                 revision="abc123", prompt="scripts/apply_bootstrap.py"):
    """Build a minimal marker dict as returned by parse_bootstrap_marker()."""
    return {
        "found": found,
        "path": "/tmp/fake/bootstrap/BOOTSTRAP_SOURCE.md",
        "source_repo": source_repo,
        "version": version,
        "revision": revision,
        "date": date,
        "agent": agent,
        "prompt": prompt,
        "profile": profile,
    }


def _write_marker(tmpdir, version="0.14.0", profile="python-service",
                  notes="N/A"):
    """
    Write a minimal BOOTSTRAP_SOURCE.md marker file to tmpdir.

    Pass notes="{{BOOTSTRAP_NOTES}}" to simulate a scaffold-applied (unpopulated)
    marker, where the notes field has not yet been filled.
    """
    bootstrap_dir = os.path.join(tmpdir, "bootstrap")
    os.makedirs(bootstrap_dir, exist_ok=True)
    path = os.path.join(bootstrap_dir, "BOOTSTRAP_SOURCE.md")
    content = (
        "# Bootstrap Source\n\n"
        "| Field | Value |\n"
        "|---|---|\n"
        f"| Bootstrap source repository | https://github.com/example/bootstrap |\n"
        f"| Bootstrap source version | {version} |\n"
        f"| Bootstrap source revision | abc123 |\n"
        f"| Bootstrap date | 2026-01-01 |\n"
        f"| Agent / operator | apply_bootstrap.py |\n"
        f"| Prompt used | scripts/apply_bootstrap.py |\n"
        f"| Bootstrap profile | {profile} |\n"
        f"\n## Bootstrap notes\n\n{notes}\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def _write_managed_file(tmpdir, rel_path, content):
    """Write a managed file at rel_path inside tmpdir."""
    full_path = os.path.join(tmpdir, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)


def _write_all_required_files(tmpdir, use_placeholders=False):
    """
    Write all TARGET_REQUIRED_FILES to tmpdir.

    If use_placeholders=True, fill files with placeholder content so doctor
    classifies the repo as scaffold-applied-unpopulated.
    If use_placeholders=False, write minimal real content.
    """
    for rel_path in bd.TARGET_REQUIRED_FILES:
        if rel_path == "bootstrap/BOOTSTRAP_SOURCE.md":
            continue  # handled separately by _write_marker
        if use_placeholders:
            _write_managed_file(tmpdir, rel_path, "{{REPO_NAME}} {{REPO_MISSION_STATEMENT}}\n")
        else:
            _write_managed_file(tmpdir, rel_path, f"# {rel_path}\nReal content.\n")


# ─────────────────────────────────────────────────────────────────────────────
# Version helper tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSemverTuple(unittest.TestCase):
    """_semver_tuple() parses version strings to int tuples."""

    def test_valid_semver(self):
        self.assertEqual(bd._semver_tuple("0.14.0"), (0, 14, 0))

    def test_valid_semver_with_major(self):
        self.assertEqual(bd._semver_tuple("1.2.3"), (1, 2, 3))

    def test_none_returns_none(self):
        self.assertIsNone(bd._semver_tuple(None))

    def test_invalid_returns_none(self):
        self.assertIsNone(bd._semver_tuple("not-semver"))

    def test_placeholder_returns_none(self):
        self.assertIsNone(bd._semver_tuple("{{BOOTSTRAP_SOURCE_VERSION}}"))


class TestIsMateriallyBehind(unittest.TestCase):
    """_is_materially_behind() compares target vs source version strings."""

    def test_same_version_not_behind(self):
        self.assertFalse(bd._is_materially_behind("0.14.0", "0.14.0"))

    def test_target_patch_behind_not_material(self):
        # Patch-only difference is NOT material
        self.assertFalse(bd._is_materially_behind("0.14.0", "0.14.1"))

    def test_target_minor_behind_is_material(self):
        self.assertTrue(bd._is_materially_behind("0.13.0", "0.14.0"))

    def test_target_major_behind_is_material(self):
        self.assertTrue(bd._is_materially_behind("0.14.0", "1.0.0"))

    def test_target_ahead_not_behind(self):
        self.assertFalse(bd._is_materially_behind("0.14.0", "0.13.0"))

    def test_none_target_not_behind(self):
        self.assertFalse(bd._is_materially_behind(None, "0.14.0"))

    def test_none_source_not_behind(self):
        self.assertFalse(bd._is_materially_behind("0.14.0", None))

    def test_invalid_strings_not_behind(self):
        self.assertFalse(bd._is_materially_behind("bad", "also-bad"))


# ─────────────────────────────────────────────────────────────────────────────
# Marker status tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMarkerStatus(unittest.TestCase):
    """marker_status() classifies marker completeness."""

    def test_missing_when_not_found(self):
        marker = _make_marker(found=False)
        self.assertEqual(bd.marker_status(marker), "missing")

    def test_present_when_all_core_fields_filled(self):
        marker = _make_marker(version="0.14.0")
        self.assertEqual(bd.marker_status(marker), "present")

    def test_incomplete_when_version_is_none(self):
        marker = _make_marker(version=None)
        self.assertEqual(bd.marker_status(marker), "incomplete")

    def test_incomplete_when_version_is_placeholder(self):
        marker = _make_marker(version="{{BOOTSTRAP_SOURCE_VERSION}}")
        self.assertEqual(bd.marker_status(marker), "incomplete")

    def test_incomplete_when_date_is_placeholder(self):
        marker = _make_marker(version="0.14.0", date="{{BOOTSTRAP_DATE}}")
        self.assertEqual(bd.marker_status(marker), "incomplete")

    def test_incomplete_when_source_repo_is_none(self):
        marker = _make_marker(version="0.14.0", source_repo=None)
        self.assertEqual(bd.marker_status(marker), "incomplete")


# ─────────────────────────────────────────────────────────────────────────────
# Required files status tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRequiredFilesStatus(unittest.TestCase):
    """required_files_status() classifies required file presence."""

    def test_all_present_when_no_missing(self):
        present = list(bd.TARGET_REQUIRED_FILES)
        missing = []
        self.assertEqual(bd.required_files_status(present, missing), "all-present")

    def test_minor_gaps_with_one_missing(self):
        present = list(bd.TARGET_REQUIRED_FILES[1:])
        missing = [bd.TARGET_REQUIRED_FILES[0]]
        self.assertEqual(bd.required_files_status(present, missing), "minor-gaps")

    def test_minor_gaps_with_two_missing(self):
        present = list(bd.TARGET_REQUIRED_FILES[2:])
        missing = list(bd.TARGET_REQUIRED_FILES[:2])
        self.assertEqual(bd.required_files_status(present, missing), "minor-gaps")

    def test_major_gaps_with_three_missing(self):
        present = list(bd.TARGET_REQUIRED_FILES[3:])
        missing = list(bd.TARGET_REQUIRED_FILES[:3])
        self.assertEqual(bd.required_files_status(present, missing), "major-gaps")

    def test_major_gaps_when_all_missing(self):
        self.assertEqual(bd.required_files_status([], list(bd.TARGET_REQUIRED_FILES)), "major-gaps")


# ─────────────────────────────────────────────────────────────────────────────
# Placeholder status tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPlaceholderStatus(unittest.TestCase):
    """placeholder_status() classifies placeholder presence across checked files."""

    def test_no_placeholders_when_all_clean(self):
        files_with = []
        files_clean = ["AGENTS.md", "IMPLEMENTATION_TRACKER.md"]
        self.assertEqual(bd.placeholder_status(files_with, files_clean, 0), "no-placeholders-detected")

    def test_placeholders_remain_when_all_dirty(self):
        files_with = ["AGENTS.md", "IMPLEMENTATION_TRACKER.md"]
        files_clean = []
        self.assertEqual(bd.placeholder_status(files_with, files_clean, 5), "placeholders-remain")

    def test_mixed_when_some_clean_some_dirty(self):
        files_with = ["AGENTS.md"]
        files_clean = ["IMPLEMENTATION_TRACKER.md"]
        self.assertEqual(bd.placeholder_status(files_with, files_clean, 2), "mixed")

    def test_no_placeholders_when_no_files_checked(self):
        self.assertEqual(bd.placeholder_status([], [], 0), "no-placeholders-detected")


# ─────────────────────────────────────────────────────────────────────────────
# Profile alignment tests
# ─────────────────────────────────────────────────────────────────────────────

class TestProfileAlignment(unittest.TestCase):
    """profile_alignment() classifies agreement between recorded and suggested profile."""

    def test_aligned_when_profiles_match(self):
        self.assertEqual(
            bd.profile_alignment("python-service", "python-service", "high"),
            "aligned",
        )

    def test_mismatch_when_profiles_differ_with_confidence(self):
        self.assertEqual(
            bd.profile_alignment("python-service", "infra-repo", "high"),
            "mismatch",
        )

    def test_mismatch_with_medium_confidence(self):
        self.assertEqual(
            bd.profile_alignment("python-service", "infra-repo", "medium"),
            "mismatch",
        )

    def test_insufficient_evidence_when_low_confidence(self):
        self.assertEqual(
            bd.profile_alignment("python-service", "infra-repo", "low"),
            "insufficient-evidence",
        )

    def test_insufficient_evidence_when_suggested_is_generic(self):
        self.assertEqual(
            bd.profile_alignment("python-service", "generic", "high"),
            "insufficient-evidence",
        )

    def test_not_recorded_when_profile_is_none(self):
        self.assertEqual(
            bd.profile_alignment(None, "python-service", "high"),
            "not-recorded",
        )

    def test_not_recorded_when_profile_is_placeholder(self):
        self.assertEqual(
            bd.profile_alignment("{{BOOTSTRAP_PROFILE}}", "python-service", "high"),
            "not-recorded",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Era classification alignment with bootstrap_core
# ─────────────────────────────────────────────────────────────────────────────

class TestClassifyEra(unittest.TestCase):
    """
    classify_era() in bootstrap_doctor delegates to bootstrap_core.classify_marker_era().

    These tests prove the two are aligned and the delegation is stable.
    """

    def _marker(self, version=None, profile=None):
        return {"version": version, "profile": profile}

    def test_pre_version_no_version(self):
        marker = self._marker()
        self.assertEqual(bd.classify_era(marker), "pre-version")
        self.assertEqual(bc.classify_marker_era(marker), "pre-version")

    def test_pre_profile_version_only(self):
        marker = self._marker(version="0.14.0")
        self.assertEqual(bd.classify_era(marker), "pre-profile")
        self.assertEqual(bc.classify_marker_era(marker), "pre-profile")

    def test_versioned_both_set(self):
        marker = self._marker(version="0.14.0", profile="python-service")
        self.assertEqual(bd.classify_era(marker), "versioned")
        self.assertEqual(bc.classify_marker_era(marker), "versioned")

    def test_unknown_non_semver_version(self):
        marker = self._marker(version="not-semver", profile="python-service")
        self.assertEqual(bd.classify_era(marker), "unknown")
        self.assertEqual(bc.classify_marker_era(marker), "unknown")

    def test_pre_version_placeholder(self):
        marker = self._marker(version="{{BOOTSTRAP_SOURCE_VERSION}}")
        self.assertEqual(bd.classify_era(marker), "pre-version")
        self.assertEqual(bc.classify_marker_era(marker), "pre-version")

    def test_doctor_and_core_always_agree(self):
        """classify_era() and classify_marker_era() must always return the same value."""
        test_cases = [
            self._marker(),
            self._marker(version="0.14.0"),
            self._marker(version="0.14.0", profile="infra-repo"),
            self._marker(version="0.14.0", profile="{{BOOTSTRAP_PROFILE}}"),
            self._marker(version="{{BOOTSTRAP_SOURCE_VERSION}}"),
            self._marker(version="not-semver", profile="generic"),
        ]
        for marker in test_cases:
            with self.subTest(marker=marker):
                self.assertEqual(bd.classify_era(marker), bc.classify_marker_era(marker))


# ─────────────────────────────────────────────────────────────────────────────
# Health classification — core states
# ─────────────────────────────────────────────────────────────────────────────

class TestClassifyHealth(unittest.TestCase):
    """
    classify_health() returns stable health state strings.

    Each test covers exactly one state to keep intent clear.
    """

    def _classify(self, marker, files_with_ph=None, files_clean=None,
                  missing_files=None, suggested_profile="generic",
                  profile_confidence="low", source_version=None):
        """Helper: call classify_health with sensible defaults."""
        if files_with_ph is None:
            files_with_ph = []
        if files_clean is None:
            files_clean = list(bd.TARGET_PLACEHOLDER_FILES)
        if missing_files is None:
            missing_files = []
        present_files = [f for f in bd.TARGET_REQUIRED_FILES if f not in missing_files]
        total_ph = sum(1 for _ in files_with_ph)
        return bd.classify_health(
            "/fake/target",
            marker,
            present_files,
            missing_files,
            files_with_ph,
            files_clean,
            total_ph,
            suggested_profile,
            profile_confidence,
            source_version,
        )

    # ── unbootstrapped ──────────────────────────────────────────────────────

    def test_unbootstrapped_when_no_marker(self):
        marker = _make_marker(found=False)
        state = self._classify(marker)
        self.assertEqual(state, "unbootstrapped")

    # ── scaffold-applied-unpopulated ────────────────────────────────────────

    def test_scaffold_applied_when_all_files_have_placeholders(self):
        marker = _make_marker(version="0.14.0", profile="python-service")
        # All checked files have placeholders, none are clean
        state = self._classify(
            marker,
            files_with_ph=list(bd.TARGET_PLACEHOLDER_FILES),
            files_clean=[],
        )
        self.assertEqual(state, "scaffold-applied-unpopulated")

    # ── partially-populated ─────────────────────────────────────────────────

    def test_partially_populated_when_some_files_have_placeholders(self):
        marker = _make_marker(version="0.14.0", profile="python-service")
        ph_files = bd.TARGET_PLACEHOLDER_FILES[:2]
        clean_files = bd.TARGET_PLACEHOLDER_FILES[2:]
        state = self._classify(
            marker,
            files_with_ph=ph_files,
            files_clean=clean_files,
        )
        self.assertEqual(state, "partially-populated")

    def test_partially_populated_when_required_files_missing(self):
        marker = _make_marker(version="0.14.0", profile="python-service")
        state = self._classify(
            marker,
            files_with_ph=[],
            files_clean=list(bd.TARGET_PLACEHOLDER_FILES),
            missing_files=["AGENTS.md"],
        )
        self.assertEqual(state, "partially-populated")

    # ── populated-and-healthy ───────────────────────────────────────────────

    def test_populated_and_healthy_when_everything_ok(self):
        marker = _make_marker(version="0.14.0", profile="python-service")
        state = self._classify(
            marker,
            files_with_ph=[],
            files_clean=list(bd.TARGET_PLACEHOLDER_FILES),
            missing_files=[],
            suggested_profile="python-service",
            profile_confidence="high",
            source_version="0.14.0",
        )
        self.assertEqual(state, "populated-and-healthy")

    def test_populated_and_healthy_when_source_version_unknown(self):
        """No source version means version drift cannot be detected — still healthy."""
        marker = _make_marker(version="0.14.0", profile="python-service")
        state = self._classify(
            marker,
            files_with_ph=[],
            files_clean=list(bd.TARGET_PLACEHOLDER_FILES),
            missing_files=[],
            source_version=None,
        )
        self.assertEqual(state, "populated-and-healthy")

    # ── stale-version-review-recommended ────────────────────────────────────

    def test_stale_version_when_minor_behind(self):
        marker = _make_marker(version="0.13.0", profile="python-service")
        state = self._classify(
            marker,
            files_with_ph=[],
            files_clean=list(bd.TARGET_PLACEHOLDER_FILES),
            missing_files=[],
            source_version="0.14.0",
        )
        self.assertEqual(state, "stale-version-review-recommended")

    def test_stale_version_when_major_behind(self):
        marker = _make_marker(version="0.14.0", profile="python-service")
        state = self._classify(
            marker,
            files_with_ph=[],
            files_clean=list(bd.TARGET_PLACEHOLDER_FILES),
            missing_files=[],
            source_version="1.0.0",
        )
        self.assertEqual(state, "stale-version-review-recommended")

    def test_not_stale_when_patch_behind_only(self):
        """Patch-only difference is not material — should not trigger stale state."""
        marker = _make_marker(version="0.14.0", profile="python-service")
        state = self._classify(
            marker,
            files_with_ph=[],
            files_clean=list(bd.TARGET_PLACEHOLDER_FILES),
            missing_files=[],
            source_version="0.14.1",
        )
        self.assertEqual(state, "populated-and-healthy")

    # ── profile-mismatch-review-recommended ─────────────────────────────────

    def test_profile_mismatch_when_confident_suggestion_differs(self):
        marker = _make_marker(version="0.14.0", profile="python-service")
        state = self._classify(
            marker,
            files_with_ph=[],
            files_clean=list(bd.TARGET_PLACEHOLDER_FILES),
            missing_files=[],
            suggested_profile="infra-repo",
            profile_confidence="high",
            source_version="0.14.0",
        )
        self.assertEqual(state, "profile-mismatch-review-recommended")

    def test_no_profile_mismatch_when_low_confidence(self):
        """Low confidence suggestion does not trigger profile mismatch."""
        marker = _make_marker(version="0.14.0", profile="python-service")
        state = self._classify(
            marker,
            files_with_ph=[],
            files_clean=list(bd.TARGET_PLACEHOLDER_FILES),
            missing_files=[],
            suggested_profile="infra-repo",
            profile_confidence="low",
            source_version="0.14.0",
        )
        self.assertEqual(state, "populated-and-healthy")

    def test_no_profile_mismatch_when_suggestion_is_generic(self):
        """Generic suggestion does not trigger profile mismatch."""
        marker = _make_marker(version="0.14.0", profile="python-service")
        state = self._classify(
            marker,
            files_with_ph=[],
            files_clean=list(bd.TARGET_PLACEHOLDER_FILES),
            missing_files=[],
            suggested_profile="generic",
            profile_confidence="high",
            source_version="0.14.0",
        )
        self.assertEqual(state, "populated-and-healthy")

    def test_stale_version_takes_priority_over_profile_mismatch(self):
        """When version is stale AND profile mismatches, stale-version wins."""
        marker = _make_marker(version="0.13.0", profile="python-service")
        state = self._classify(
            marker,
            files_with_ph=[],
            files_clean=list(bd.TARGET_PLACEHOLDER_FILES),
            missing_files=[],
            suggested_profile="infra-repo",
            profile_confidence="high",
            source_version="0.14.0",
        )
        self.assertEqual(state, "stale-version-review-recommended")


# ─────────────────────────────────────────────────────────────────────────────
# Recommend actions
# ─────────────────────────────────────────────────────────────────────────────

class TestRecommendActions(unittest.TestCase):
    """recommend_actions() returns sensible next-step commands for each state."""

    def _recommend(self, state, td="/fake/target", suggested_profile="generic",
                   source_version=None, missing_files=None):
        marker = _make_marker(version="0.14.0", profile="python-service")
        return bd.recommend_actions(
            state, td, marker, missing_files or [], suggested_profile, source_version
        )

    def test_unbootstrapped_suggests_apply(self):
        cmds = self._recommend("unbootstrapped")
        joined = "\n".join(cmds)
        self.assertIn("suggest_profile.py", joined)
        self.assertIn("apply_bootstrap.py", joined)
        self.assertIn("--dry-run", joined)

    def test_unbootstrapped_includes_profile_flag_when_non_generic(self):
        cmds = self._recommend("unbootstrapped", suggested_profile="python-service")
        apply_cmd = next(c for c in cmds if "apply_bootstrap.py" in c)
        self.assertIn("--profile python-service", apply_cmd)

    def test_unbootstrapped_omits_profile_flag_for_generic(self):
        cmds = self._recommend("unbootstrapped", suggested_profile="generic")
        apply_cmd = next(c for c in cmds if "apply_bootstrap.py" in c)
        self.assertNotIn("--profile", apply_cmd)

    def test_scaffold_applied_suggests_validate(self):
        cmds = self._recommend("scaffold-applied-unpopulated")
        joined = "\n".join(cmds)
        self.assertIn("validate_bootstrap.py", joined)

    def test_partially_populated_suggests_validate(self):
        cmds = self._recommend("partially-populated")
        joined = "\n".join(cmds)
        self.assertIn("validate_bootstrap.py", joined)

    def test_populated_and_healthy_suggests_validate_and_status(self):
        cmds = self._recommend("populated-and-healthy")
        joined = "\n".join(cmds)
        self.assertIn("validate_bootstrap.py", joined)
        self.assertIn("bootstrap_status.py", joined)

    def test_stale_version_suggests_refresh_dry_run(self):
        cmds = self._recommend("stale-version-review-recommended",
                               source_version="0.14.0")
        joined = "\n".join(cmds)
        self.assertIn("refresh_bootstrap.py", joined)
        self.assertIn("--dry-run", joined)

    def test_profile_mismatch_suggests_suggest_and_status(self):
        cmds = self._recommend("profile-mismatch-review-recommended")
        joined = "\n".join(cmds)
        self.assertIn("suggest_profile.py", joined)
        self.assertIn("bootstrap_status.py", joined)

    def test_no_force_flag_in_any_recommendation(self):
        """Conservative: recommendations must never include --force by default."""
        states = [
            "unbootstrapped",
            "scaffold-applied-unpopulated",
            "partially-populated",
            "populated-and-healthy",
            "stale-version-review-recommended",
            "profile-mismatch-review-recommended",
        ]
        for state in states:
            cmds = self._recommend(state)
            joined = "\n".join(cmds)
            with self.subTest(state=state):
                self.assertNotIn("--force", joined)


# ─────────────────────────────────────────────────────────────────────────────
# Health state names — stability contract
# ─────────────────────────────────────────────────────────────────────────────

class TestHealthStateNames(unittest.TestCase):
    """
    The six health state names are a stable operator contract.

    They must not be renamed or removed without a version bump.
    These tests prove the names exist and are distinct.
    """

    EXPECTED_STATES = {
        "unbootstrapped",
        "scaffold-applied-unpopulated",
        "partially-populated",
        "populated-and-healthy",
        "stale-version-review-recommended",
        "profile-mismatch-review-recommended",
    }

    def test_health_labels_covers_all_states(self):
        self.assertEqual(set(bd.HEALTH_LABELS.keys()), self.EXPECTED_STATES)

    def test_health_descriptions_covers_all_states(self):
        self.assertEqual(set(bd.HEALTH_DESCRIPTIONS.keys()), self.EXPECTED_STATES)

    def test_all_states_are_distinct_strings(self):
        self.assertEqual(len(self.EXPECTED_STATES), 6)


# ─────────────────────────────────────────────────────────────────────────────
# Integration: audit() with synthetic temp dirs
# ─────────────────────────────────────────────────────────────────────────────

class TestAuditIntegration(unittest.TestCase):
    """
    End-to-end tests for audit() using real temporary directories.

    These prove the full classification pipeline works for the key states.
    """

    def test_unbootstrapped_empty_dir(self):
        """An empty directory is classified as unbootstrapped."""
        with tempfile.TemporaryDirectory() as d:
            result = bd.audit(d, _REPO_ROOT)
        self.assertEqual(result["health_state"], "unbootstrapped")
        self.assertFalse(result["bootstrapped"])

    def test_scaffold_applied_unpopulated(self):
        """Directory with marker + placeholder-filled files → scaffold-applied-unpopulated."""
        with tempfile.TemporaryDirectory() as d:
            # apply_bootstrap.py fills system fields in the marker but leaves
            # {{BOOTSTRAP_NOTES}} unfilled — so the marker itself has a placeholder.
            _write_marker(d, version="0.14.0", profile="python-service",
                          notes="{{BOOTSTRAP_NOTES}}")
            _write_all_required_files(d, use_placeholders=True)
            result = bd.audit(d, _REPO_ROOT)
        self.assertEqual(result["health_state"], "scaffold-applied-unpopulated")

    def test_populated_and_healthy(self):
        """Directory with marker + real content files → populated-and-healthy."""
        # Use the actual current source version so the repo is not considered stale.
        current_version, _ = bc.read_version(_REPO_ROOT)
        marker_version = current_version or "0.15.0"
        with tempfile.TemporaryDirectory() as d:
            _write_marker(d, version=marker_version, profile="python-service")
            _write_all_required_files(d, use_placeholders=False)
            result = bd.audit(d, _REPO_ROOT)
        self.assertEqual(result["health_state"], "populated-and-healthy")

    def test_partially_populated(self):
        """Some files have real content, some have placeholders → partially-populated."""
        with tempfile.TemporaryDirectory() as d:
            _write_marker(d, version="0.14.0", profile="python-service")
            # Write half the managed files with placeholders, half with real content
            ph_files = bd.TARGET_PLACEHOLDER_FILES[:2]
            real_files = bd.TARGET_PLACEHOLDER_FILES[2:]
            for rel_path in ph_files:
                _write_managed_file(d, rel_path, "{{REPO_NAME}} {{REPO_MISSION_STATEMENT}}\n")
            for rel_path in real_files:
                _write_managed_file(d, rel_path, f"# {rel_path}\nReal content.\n")
            # Write non-placeholder required files
            _write_managed_file(d, "artifacts/ai/repo_discovery.json",
                                '{"repo_name": "test-repo"}\n')
            result = bd.audit(d, _REPO_ROOT)
        self.assertEqual(result["health_state"], "partially-populated")

    def test_stale_version(self):
        """Populated repo with old bootstrap version → stale-version-review-recommended."""
        with tempfile.TemporaryDirectory() as d:
            # Write a marker with a very old version
            _write_marker(d, version="0.1.0", profile="python-service")
            _write_all_required_files(d, use_placeholders=False)
            result = bd.audit(d, _REPO_ROOT)
        # Only meaningful if source version is known and materially newer
        source_ver = result["source_version"]
        if source_ver and bd._is_materially_behind("0.1.0", source_ver):
            self.assertEqual(result["health_state"], "stale-version-review-recommended")
        else:
            # source version not readable in test environment — skip stale check
            self.assertIn(result["health_state"],
                          {"populated-and-healthy", "stale-version-review-recommended"})

    def test_audit_result_keys_stable(self):
        """audit() must always return the documented set of result keys."""
        expected_keys = {
            "target_dir", "bootstrapped", "marker_status", "marker_era",
            "recorded_version", "source_version", "recorded_profile",
            "suggested_profile", "profile_confidence", "profile_alignment",
            "required_files_status", "present_files", "missing_files",
            "placeholder_status", "files_with_placeholders", "files_clean",
            "total_placeholder_count", "health_state", "recommendations",
        }
        with tempfile.TemporaryDirectory() as d:
            result = bd.audit(d, _REPO_ROOT)
        self.assertEqual(set(result.keys()), expected_keys)

    def test_audit_read_only(self):
        """audit() must not create or modify any files in the target directory."""
        with tempfile.TemporaryDirectory() as d:
            before = set(os.listdir(d))
            bd.audit(d, _REPO_ROOT)
            after = set(os.listdir(d))
        self.assertEqual(before, after, "audit() must not modify the target directory")


# ─────────────────────────────────────────────────────────────────────────────
# Cross-tool alignment: doctor and bootstrap_core agree on marker era
# ─────────────────────────────────────────────────────────────────────────────

class TestDoctorCoreAlignment(unittest.TestCase):
    """
    Prove that bootstrap_doctor and bootstrap_core stay semantically aligned on
    shared helpers (marker parsing, era classification).
    """

    def test_parse_marker_delegates_to_core(self):
        """bootstrap_doctor.parse_marker() must produce same result as bootstrap_core."""
        with tempfile.TemporaryDirectory() as d:
            bootstrap_dir = os.path.join(d, "bootstrap")
            os.makedirs(bootstrap_dir)
            marker_content = (
                "| Bootstrap source version | 0.14.0 |\n"
                "| Bootstrap profile | python-service |\n"
            )
            with open(os.path.join(bootstrap_dir, "BOOTSTRAP_SOURCE.md"), "w") as f:
                f.write(marker_content)
            doctor_result = bd.parse_marker(d)
            core_result = bc.parse_bootstrap_marker(d)
        self.assertEqual(doctor_result["version"], core_result["version"])
        self.assertEqual(doctor_result["profile"], core_result["profile"])
        self.assertEqual(doctor_result["found"], core_result["found"])

    def test_era_classification_agrees_for_all_eras(self):
        """
        For every era, doctor and core must return the same string.

        This proves classify_era() faithfully delegates to classify_marker_era().
        """
        era_markers = [
            {"version": None, "profile": None},
            {"version": "{{BOOTSTRAP_SOURCE_VERSION}}", "profile": None},
            {"version": "0.14.0", "profile": None},
            {"version": "0.14.0", "profile": "{{BOOTSTRAP_PROFILE}}"},
            {"version": "0.14.0", "profile": "python-service"},
            {"version": "not-semver", "profile": "python-service"},
        ]
        for marker in era_markers:
            with self.subTest(marker=marker):
                self.assertEqual(
                    bd.classify_era(marker),
                    bc.classify_marker_era(marker),
                )

    def test_required_files_list_matches_expected_count(self):
        """
        TARGET_REQUIRED_FILES must have the documented number of entries (7).

        If this count changes, it is a deliberate contract expansion and must
        be accompanied by a version bump and documentation update.
        """
        self.assertEqual(len(bd.TARGET_REQUIRED_FILES), 7)

    def test_placeholder_files_subset_of_required_files(self):
        """Every placeholder file must also be in the required files list."""
        required_set = set(bd.TARGET_REQUIRED_FILES)
        for rel_path in bd.TARGET_PLACEHOLDER_FILES:
            with self.subTest(rel_path=rel_path):
                self.assertIn(rel_path, required_set)


if __name__ == "__main__":
    unittest.main()
