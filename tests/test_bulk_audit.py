"""
Contract tests for bulk_audit.py

Tests cover:
  - explicit --repo path handling
  - root-dir repo discovery
  - aggregate counts by health state
  - JSON output shape
  - handling of unreadable/missing repos
  - read-only behavior (no mutations)
  - schema presence and parseability

Run with:
    python -m unittest discover -s tests -p 'test_*.py'
or:
    python -m unittest tests/test_bulk_audit.py
"""

import json
import os
import sys
import tempfile
import unittest

# Ensure the scripts directory is on the path
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS_DIR = os.path.join(_REPO_ROOT, "scripts")
_SCHEMAS_DIR = os.path.join(_REPO_ROOT, "schemas")
sys.path.insert(0, _SCRIPTS_DIR)

import bulk_audit as ba
import bootstrap_doctor as bd


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_git_repo(parent_dir, name):
    """Create a minimal git-repo-shaped directory under parent_dir."""
    repo_dir = os.path.join(parent_dir, name)
    os.makedirs(os.path.join(repo_dir, ".git"), exist_ok=True)
    with open(os.path.join(repo_dir, "README.md"), "w") as f:
        f.write(f"# {name}\n")
    return repo_dir


def _make_non_git_dir(parent_dir, name):
    """Create a plain directory (not a git repo) under parent_dir."""
    d = os.path.join(parent_dir, name)
    os.makedirs(d, exist_ok=True)
    return d


def _write_marker(tmpdir, version="0.15.0", profile="python-service"):
    """Write a minimal BOOTSTRAP_SOURCE.md marker to tmpdir."""
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
    )
    with open(path, "w") as f:
        f.write(content)


def _write_managed_file(tmpdir, rel_path, content="# Real content\n"):
    """Write a managed file at rel_path inside tmpdir."""
    full_path = os.path.join(tmpdir, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)


def _write_all_required_files(tmpdir):
    """Write all TARGET_REQUIRED_FILES with real content (no placeholders)."""
    for rel_path in bd.TARGET_REQUIRED_FILES:
        if rel_path == "bootstrap/BOOTSTRAP_SOURCE.md":
            continue
        _write_managed_file(tmpdir, rel_path, f"# {rel_path}\nReal content.\n")


# ─────────────────────────────────────────────────────────────────────────────
# Repo discovery tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDiscoverRepos(unittest.TestCase):
    """discover_repos() finds git repos under a root directory."""

    def test_finds_git_repos(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            r1 = _make_git_repo(tmpdir, "repo-a")
            r2 = _make_git_repo(tmpdir, "repo-b")
            found = ba.discover_repos(tmpdir)
            self.assertIn(r1, found)
            self.assertIn(r2, found)
            self.assertEqual(len(found), 2)

    def test_ignores_non_git_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            r1 = _make_git_repo(tmpdir, "repo-a")
            _make_non_git_dir(tmpdir, "not-a-repo")
            found = ba.discover_repos(tmpdir)
            self.assertEqual(found, [r1])

    def test_max_depth_1_is_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            r1 = _make_git_repo(tmpdir, "repo-a")
            # Nested repo at depth 2 — should not be found at max_depth=1
            subdir = _make_non_git_dir(tmpdir, "level1")
            _make_git_repo(subdir, "nested-repo")
            found = ba.discover_repos(tmpdir, max_depth=1)
            self.assertIn(r1, found)
            self.assertEqual(len(found), 1)

    def test_max_depth_2_finds_nested(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = _make_non_git_dir(tmpdir, "group")
            r1 = _make_git_repo(subdir, "nested-repo")
            found = ba.discover_repos(tmpdir, max_depth=2)
            self.assertIn(r1, found)
            self.assertEqual(len(found), 1)

    def test_empty_root_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            found = ba.discover_repos(tmpdir)
            self.assertEqual(found, [])

    def test_result_is_sorted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_git_repo(tmpdir, "z-repo")
            _make_git_repo(tmpdir, "a-repo")
            found = ba.discover_repos(tmpdir)
            self.assertEqual(found, sorted(found))


# ─────────────────────────────────────────────────────────────────────────────
# Per-repo audit tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAuditRepo(unittest.TestCase):
    """audit_repo() returns structured results or error strings."""

    def test_missing_dir_returns_error(self):
        result, err = ba.audit_repo("/nonexistent/path/to/repo", _REPO_ROOT)
        self.assertIsNone(result)
        self.assertIsNotNone(err)
        self.assertIn("not a directory", err)

    def test_unbootstrapped_repo_returns_result(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result, err = ba.audit_repo(tmpdir, _REPO_ROOT)
            self.assertIsNone(err)
            self.assertIsNotNone(result)
            self.assertEqual(result["health_state"], "unbootstrapped")

    def test_populated_repo_returns_healthy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_marker(tmpdir)
            _write_all_required_files(tmpdir)
            result, err = ba.audit_repo(tmpdir, _REPO_ROOT)
            self.assertIsNone(err)
            self.assertIn(result["health_state"], [
                "populated-and-healthy",
                "stale-version-review-recommended",
            ])

    def test_result_has_required_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result, err = ba.audit_repo(tmpdir, _REPO_ROOT)
            self.assertIsNone(err)
            for field in ("target_dir", "bootstrapped", "health_state",
                          "marker_status", "marker_era", "required_files_status",
                          "missing_files", "placeholder_status",
                          "total_placeholder_count"):
                self.assertIn(field, result, f"missing field: {field}")


# ─────────────────────────────────────────────────────────────────────────────
# Aggregate summary tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildSummary(unittest.TestCase):
    """build_summary() produces correct aggregate counts."""

    def _make_result(self, health_state, recorded_profile=None, suggested_profile="generic"):
        return {
            "health_state": health_state,
            "recorded_profile": recorded_profile,
            "suggested_profile": suggested_profile,
        }

    def test_empty_returns_all_zero_health_states(self):
        summary = ba.build_summary([])
        for state in ba.ALL_HEALTH_STATES:
            self.assertEqual(summary["by_health_state"][state], 0)

    def test_counts_health_states(self):
        results = [
            self._make_result("populated-and-healthy", "python-service"),
            self._make_result("populated-and-healthy", "infra-repo"),
            self._make_result("unbootstrapped"),
        ]
        summary = ba.build_summary(results)
        self.assertEqual(summary["by_health_state"]["populated-and-healthy"], 2)
        self.assertEqual(summary["by_health_state"]["unbootstrapped"], 1)

    def test_counts_profiles_using_recorded_when_available(self):
        results = [
            self._make_result("populated-and-healthy", "python-service", "python-service"),
            self._make_result("populated-and-healthy", "infra-repo", "python-service"),
        ]
        summary = ba.build_summary(results)
        self.assertEqual(summary["by_profile"]["python-service"], 1)
        self.assertEqual(summary["by_profile"]["infra-repo"], 1)

    def test_falls_back_to_suggested_profile_when_no_recorded(self):
        results = [
            self._make_result("unbootstrapped", None, "python-service"),
        ]
        summary = ba.build_summary(results)
        self.assertEqual(summary["by_profile"].get("python-service", 0), 1)


class TestHighPriorityRepos(unittest.TestCase):
    """high_priority_repos() filters to attention-needed repos."""

    def _make_result(self, health_state, target_dir="/tmp/repo"):
        return {"health_state": health_state, "target_dir": target_dir}

    def test_includes_unbootstrapped(self):
        r = self._make_result("unbootstrapped")
        result = ba.high_priority_repos([r])
        self.assertIn(r, result)

    def test_excludes_healthy(self):
        r = self._make_result("populated-and-healthy")
        result = ba.high_priority_repos([r])
        self.assertNotIn(r, result)

    def test_includes_stale(self):
        r = self._make_result("stale-version-review-recommended")
        result = ba.high_priority_repos([r])
        self.assertIn(r, result)

    def test_includes_mismatch(self):
        r = self._make_result("profile-mismatch-review-recommended")
        result = ba.high_priority_repos([r])
        self.assertIn(r, result)

    def test_includes_partially_populated(self):
        r = self._make_result("partially-populated")
        result = ba.high_priority_repos([r])
        self.assertIn(r, result)


# ─────────────────────────────────────────────────────────────────────────────
# JSON output shape tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildJsonReport(unittest.TestCase):
    """build_json_report() produces the expected JSON structure."""

    def setUp(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.result, _ = ba.audit_repo(tmpdir, _REPO_ROOT)

    def test_top_level_required_keys(self):
        report = ba.build_json_report([self.result], [], "0.15.0")
        for key in ("schema_version", "generated_at", "bootstrap_source_version",
                    "repo_count", "summary", "repos", "errors"):
            self.assertIn(key, report, f"missing key: {key}")

    def test_schema_version(self):
        report = ba.build_json_report([], [], "0.15.0")
        self.assertEqual(report["schema_version"], ba.BULK_REPORT_SCHEMA_VERSION)

    def test_repo_count(self):
        report = ba.build_json_report([self.result], [("/bad", "err")], "0.15.0")
        self.assertEqual(report["repo_count"], 2)

    def test_errors_structure(self):
        errors = [("/bad/path", "not a directory")]
        report = ba.build_json_report([], errors, "0.15.0")
        self.assertEqual(len(report["errors"]), 1)
        self.assertEqual(report["errors"][0]["repo_path"], "/bad/path")
        self.assertEqual(report["errors"][0]["error"], "not a directory")

    def test_repos_contains_per_repo_results(self):
        report = ba.build_json_report([self.result], [], "0.15.0")
        self.assertEqual(len(report["repos"]), 1)

    def test_per_repo_has_required_fields(self):
        """Per-repo entries must contain all doctor-schema required fields (minus schema_version)."""
        schema_path = os.path.join(
            _REPO_ROOT, "schemas", "bootstrap_doctor_report.schema.json"
        )
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        doctor_required = set(schema["required"]) - {"schema_version"}

        report = ba.build_json_report([self.result], [], "0.15.0")
        repo = report["repos"][0]
        for field in doctor_required:
            self.assertIn(field, repo, f"per-repo entry missing doctor-required field: {field}")

    def test_summary_has_expected_keys(self):
        report = ba.build_json_report([self.result], [], "0.15.0")
        self.assertIn("by_health_state", report["summary"])
        self.assertIn("by_profile", report["summary"])

    def test_generated_at_format(self):
        import re
        report = ba.build_json_report([], [], None)
        self.assertRegex(
            report["generated_at"],
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$",
        )

    def test_report_is_json_serialisable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            r, _ = ba.audit_repo(tmpdir, _REPO_ROOT)
        report = ba.build_json_report([r], [], "0.15.0")
        # Should not raise
        text = json.dumps(report)
        self.assertIsInstance(text, str)


class TestRepoResultToJson(unittest.TestCase):
    """_repo_result_to_json() converts audit result to JSON-safe shape."""

    @classmethod
    def _load_doctor_required_fields(cls):
        """Load required fields from the doctor schema, excluding schema_version."""
        schema_path = os.path.join(
            _REPO_ROOT, "schemas", "bootstrap_doctor_report.schema.json"
        )
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        return set(schema["required"]) - {"schema_version"}

    def _get_per_repo_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result, _ = ba.audit_repo(tmpdir, _REPO_ROOT)
        return ba._repo_result_to_json(result)

    def test_all_doctor_required_fields_present(self):
        """Every doctor-schema required field (except schema_version) must appear."""
        doctor_required = self._load_doctor_required_fields()
        out = self._get_per_repo_output()
        for field in doctor_required:
            self.assertIn(field, out, f"missing doctor-required field: {field}")

    def test_schema_version_intentionally_absent_per_repo(self):
        """schema_version lives at the bulk report level, not per-repo."""
        out = self._get_per_repo_output()
        self.assertNotIn(
            "schema_version", out,
            "schema_version must NOT appear in per-repo entries; "
            "it belongs at the bulk report top level only.",
        )

    def test_optional_doctor_fields_included(self):
        """Optional doctor fields should also be present in per-repo output."""
        out = self._get_per_repo_output()
        for field in ("recorded_version", "source_version", "recorded_profile",
                      "suggested_profile", "profile_confidence", "profile_alignment"):
            self.assertIn(field, out, f"optional doctor field missing from per-repo: {field}")

    def test_recommendations_are_structured(self):
        out = self._get_per_repo_output()
        for rec in out["recommendations"]:
            self.assertIn("type", rec)
            self.assertIn("value", rec)
            self.assertIn(rec["type"], ("command", "note"))

    def test_field_alignment_matches_doctor_schema(self):
        """
        Bulk per-repo fields must be a superset of doctor schema required fields
        (minus schema_version).  This test is the anti-drift guard: if the doctor
        schema adds a new required field, this test will fail, prompting an update
        to _repo_result_to_json().
        """
        doctor_required = self._load_doctor_required_fields()
        out = self._get_per_repo_output()
        missing = doctor_required - set(out.keys())
        self.assertEqual(
            missing,
            set(),
            f"Bulk per-repo output is missing doctor-required fields: {missing}. "
            "Update _repo_result_to_json() in bulk_audit.py to include them.",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Read-only behavior tests
# ─────────────────────────────────────────────────────────────────────────────

class TestReadOnlyBehaviour(unittest.TestCase):
    """bulk_audit must not modify any repository."""

    def test_audit_does_not_modify_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Record file tree before audit
            before = set()
            for root, dirs, files in os.walk(tmpdir):
                for f in files:
                    before.add(os.path.join(root, f))

            ba.audit_repo(tmpdir, _REPO_ROOT)

            # Record file tree after audit
            after = set()
            for root, dirs, files in os.walk(tmpdir):
                for f in files:
                    after.add(os.path.join(root, f))

            self.assertEqual(before, after, "audit_repo must not create or modify files")

    def test_discover_repos_does_not_modify_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_git_repo(tmpdir, "repo-a")
            before = set()
            for root, dirs, files in os.walk(tmpdir):
                for f in files:
                    before.add(os.path.join(root, f))

            ba.discover_repos(tmpdir)

            after = set()
            for root, dirs, files in os.walk(tmpdir):
                for f in files:
                    after.add(os.path.join(root, f))

            self.assertEqual(before, after)


# ─────────────────────────────────────────────────────────────────────────────
# Fixture-based integration test
# ─────────────────────────────────────────────────────────────────────────────

class TestFixtureIntegration(unittest.TestCase):
    """
    Bulk audit on the existing fixture repos produces expected health states.

    Uses the fixture directories directly (without a temp copy) since
    bulk_audit is read-only and will not modify them.
    """

    def setUp(self):
        self.fixtures_dir = os.path.join(_REPO_ROOT, "fixtures", "targets")
        self.py_fixture = os.path.join(self.fixtures_dir, "minimal-python-service")
        self.infra_fixture = os.path.join(self.fixtures_dir, "minimal-infra-repo")

    def test_both_fixtures_return_unbootstrapped_when_raw(self):
        """Raw fixtures have no bootstrap marker — expect unbootstrapped."""
        for fixture in (self.py_fixture, self.infra_fixture):
            result, err = ba.audit_repo(fixture, _REPO_ROOT)
            self.assertIsNone(err, f"Unexpected error for {fixture}: {err}")
            self.assertEqual(
                result["health_state"],
                "unbootstrapped",
                f"Expected unbootstrapped for raw fixture {os.path.basename(fixture)}",
            )

    def test_bulk_audit_produces_coherent_summary(self):
        """Auditing both fixtures produces a coherent aggregate summary."""
        results = []
        errors = []
        for fixture in (self.py_fixture, self.infra_fixture):
            r, e = ba.audit_repo(fixture, _REPO_ROOT)
            if e:
                errors.append((fixture, e))
            else:
                results.append(r)

        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 2)

        summary = ba.build_summary(results)
        # Both fixtures are raw → unbootstrapped
        self.assertEqual(summary["by_health_state"]["unbootstrapped"], 2)

    def test_json_report_is_valid_json(self):
        results = []
        for fixture in (self.py_fixture, self.infra_fixture):
            r, _ = ba.audit_repo(fixture, _REPO_ROOT)
            if r:
                results.append(r)
        report = ba.build_json_report(results, [], "0.15.0")
        text = json.dumps(report)
        parsed = json.loads(text)
        self.assertEqual(parsed["repo_count"], 2)


# ─────────────────────────────────────────────────────────────────────────────
# Schema presence and parseability tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBulkSchemaPresence(unittest.TestCase):
    """The bulk audit JSON schema file must exist and be parseable."""

    def test_schema_file_exists(self):
        schema_path = os.path.join(
            _REPO_ROOT, "schemas", "bootstrap_bulk_audit_report.schema.json"
        )
        self.assertTrue(
            os.path.isfile(schema_path),
            f"Schema file not found: {schema_path}",
        )

    def test_schema_is_valid_json(self):
        schema_path = os.path.join(
            _REPO_ROOT, "schemas", "bootstrap_bulk_audit_report.schema.json"
        )
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        self.assertIsInstance(schema, dict)

    def test_schema_has_required_top_level_keys(self):
        schema_path = os.path.join(
            _REPO_ROOT, "schemas", "bootstrap_bulk_audit_report.schema.json"
        )
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        for key in ("schema_version", "generated_at", "bootstrap_source_version",
                    "repo_count", "summary", "repos", "errors"):
            self.assertIn(key, schema["properties"], f"schema missing property: {key}")


# ─────────────────────────────────────────────────────────────────────────────
# Error-handling tests
# ─────────────────────────────────────────────────────────────────────────────

class TestErrorHandling(unittest.TestCase):
    """Errors for one repo do not prevent auditing other repos."""

    def test_error_does_not_stop_processing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            good_repo = tmpdir  # a valid directory
            bad_repo = "/nonexistent/totally/missing"

            good_result, good_err = ba.audit_repo(good_repo, _REPO_ROOT)
            bad_result, bad_err = ba.audit_repo(bad_repo, _REPO_ROOT)

            self.assertIsNone(good_err)
            self.assertIsNotNone(bad_err)
            self.assertIsNone(bad_result)

    def test_json_report_captures_errors(self):
        errors = [("/missing/repo", "not a directory")]
        report = ba.build_json_report([], errors, "0.15.0")
        self.assertEqual(len(report["errors"]), 1)
        self.assertEqual(report["errors"][0]["repo_path"], "/missing/repo")

    def test_mixed_batch_partial_failure(self):
        """
        A batch with one good repo and one bad path must produce:
          - one successful result in repos[]
          - one error entry in errors[]
        This proves the audit loop is partial-failure tolerant — one failure
        does not stop the rest of the batch.
        """
        with tempfile.TemporaryDirectory() as good_dir:
            bad_path = "/nonexistent/repo/path"

            repo_results = []
            errors = []
            for path in (good_dir, bad_path):
                result, err = ba.audit_repo(path, _REPO_ROOT)
                if err:
                    errors.append((path, err))
                else:
                    repo_results.append(result)

            self.assertEqual(len(repo_results), 1, "good repo must produce a result")
            self.assertEqual(len(errors), 1, "bad path must produce exactly one error")
            self.assertIn("not a directory", errors[0][1])
            self.assertEqual(repo_results[0]["health_state"], "unbootstrapped")

    def test_all_repos_fail_still_produces_report(self):
        """
        When every repo in the batch fails, build_json_report still produces
        a valid (empty-repos) report.  No exception must be raised.
        """
        errors = [
            ("/nonexistent/a", "not a directory"),
            ("/nonexistent/b", "not a directory"),
        ]
        report = ba.build_json_report([], errors, "0.15.0")
        self.assertEqual(report["repo_count"], 2)
        self.assertEqual(report["repos"], [])
        self.assertEqual(len(report["errors"]), 2)
        # Summary over zero results must not raise
        self.assertIn("by_health_state", report["summary"])

    def test_repo_flag_accepts_non_git_directory(self):
        """
        --repo accepts any existing directory, regardless of whether it
        contains .git/.  This is different from --root-dir, which skips
        directories without .git/.  A non-git dir is audited and classified
        as 'unbootstrapped' (no bootstrap marker).
        """
        with tempfile.TemporaryDirectory() as non_git_dir:
            # Confirm no .git/ exists
            self.assertFalse(os.path.isdir(os.path.join(non_git_dir, ".git")))
            result, err = ba.audit_repo(non_git_dir, _REPO_ROOT)
            self.assertIsNone(err, "non-git dir must not produce an error")
            self.assertIsNotNone(result)
            self.assertEqual(
                result["health_state"],
                "unbootstrapped",
                "--repo with a non-git dir must return unbootstrapped, not an error",
            )

    def test_root_dir_skips_non_git_directories(self):
        """
        --root-dir skips directories that do not contain .git/.
        This is the conservative behavior documented in the module docstring
        and --root-dir help text.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a plain dir (no .git/)
            plain_dir = os.path.join(tmpdir, "plain-dir")
            os.makedirs(plain_dir)
            # Create a git repo
            git_repo = _make_git_repo(tmpdir, "git-repo")

            found = ba.discover_repos(tmpdir, max_depth=1)
            self.assertIn(git_repo, found)
            self.assertNotIn(plain_dir, found)


if __name__ == "__main__":
    unittest.main()
