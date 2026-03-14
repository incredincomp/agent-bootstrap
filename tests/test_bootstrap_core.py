"""
Contract tests for bootstrap_core.py

These tests prove that the shared semantic helpers in bootstrap_core.py remain
stable and aligned.  They are intentionally small and explicit.

Run with:
    python -m unittest discover -s tests -p 'test_*.py'
or:
    python -m unittest tests/test_bootstrap_core.py
"""

import os
import sys
import tempfile
import unittest

# Ensure the scripts directory is on the path so bootstrap_core can be imported
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS_DIR = os.path.join(_REPO_ROOT, "scripts")
sys.path.insert(0, _SCRIPTS_DIR)

import bootstrap_core as bc


class TestRegexConstants(unittest.TestCase):
    """PLACEHOLDER_RE and SEMVER_RE are stable contracts."""

    def test_placeholder_re_matches_token(self):
        self.assertIsNotNone(bc.PLACEHOLDER_RE.search("{{REPO_NAME}}"))

    def test_placeholder_re_matches_mixed_text(self):
        self.assertIsNotNone(bc.PLACEHOLDER_RE.search("Hello {{WORLD}}!"))

    def test_placeholder_re_rejects_lowercase(self):
        self.assertIsNone(bc.PLACEHOLDER_RE.search("{{not_a_placeholder}}"))

    def test_placeholder_re_rejects_plain_text(self):
        self.assertIsNone(bc.PLACEHOLDER_RE.search("no placeholders here"))

    def test_semver_re_matches(self):
        for v in ("0.13.0", "1.0.0", "2.11.3"):
            with self.subTest(v=v):
                self.assertIsNotNone(bc.SEMVER_RE.match(v))

    def test_semver_re_rejects(self):
        for v in ("v1.0.0", "1.0", "abc", ""):
            with self.subTest(v=v):
                self.assertIsNone(bc.SEMVER_RE.match(v))


class TestReadVersion(unittest.TestCase):
    """read_version() reads the VERSION file and validates semver."""

    def test_reads_valid_version(self):
        version, err = bc.read_version(_REPO_ROOT)
        self.assertIsNone(err, f"Expected no error but got: {err}")
        self.assertIsNotNone(version)
        self.assertRegex(version, r"^\d+\.\d+\.\d+")

    def test_missing_file_returns_error(self):
        version, err = bc.read_version("/nonexistent/dir")
        self.assertIsNone(version)
        self.assertIsNotNone(err)

    def test_nonsemver_file_returns_error(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "VERSION"), "w") as f:
                f.write("not-a-version\n")
            version, err = bc.read_version(d)
            self.assertEqual(version, "not-a-version")
            self.assertIsNotNone(err)


class TestLoadManifest(unittest.TestCase):
    """load_manifest() reads the bootstrap-manifest.yaml as raw text."""

    def test_loads_manifest(self):
        content = bc.load_manifest(_REPO_ROOT)
        self.assertIsNotNone(content)
        self.assertIn("bootstrap-manifest", content)

    def test_missing_returns_none(self):
        content = bc.load_manifest("/nonexistent/dir")
        self.assertIsNone(content)


class TestProfiles(unittest.TestCase):
    """Profile helpers return stable, consistent data."""

    EXPECTED_PROFILES = {
        "generic",
        "python-service",
        "infra-repo",
        "vscode-extension",
        "kubernetes-platform",
    }

    def test_get_supported_profiles_contains_expected(self):
        profiles = bc.get_supported_profiles()
        self.assertEqual(set(profiles), self.EXPECTED_PROFILES)

    def test_get_supported_profiles_is_sorted(self):
        profiles = bc.get_supported_profiles()
        self.assertEqual(profiles, sorted(profiles))

    def test_resolve_profile_valid(self):
        for name in self.EXPECTED_PROFILES:
            with self.subTest(name=name):
                self.assertEqual(bc.resolve_profile(name), name)

    def test_resolve_profile_invalid_raises(self):
        with self.assertRaises(ValueError):
            bc.resolve_profile("nonexistent-profile")


class TestResolveTemplateMappings(unittest.TestCase):
    """Template mappings include the right sources for each profile."""

    def test_generic_uses_base_template(self):
        mappings = bc.resolve_template_mappings("generic")
        kb_map = next(
            m for m in mappings
            if m["destination"] == "docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md"
        )
        self.assertIn("AI_AGENT_VENDOR_KNOWLEDGE_BASE.md.template", kb_map["source"])
        self.assertNotIn("profiles/", kb_map["source"])

    def test_python_service_overrides_kb(self):
        mappings = bc.resolve_template_mappings("python-service")
        kb_map = next(
            m for m in mappings
            if m["destination"] == "docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md"
        )
        self.assertIn("python-service", kb_map["source"])

    def test_infra_repo_overrides_kb(self):
        mappings = bc.resolve_template_mappings("infra-repo")
        kb_map = next(
            m for m in mappings
            if m["destination"] == "docs/ai/AI_AGENT_VENDOR_KNOWLEDGE_BASE.md"
        )
        self.assertIn("infra-repo", kb_map["source"])

    def test_all_profiles_have_same_destinations(self):
        """Every profile produces the same set of destination paths."""
        base_dests = {m["destination"] for m in bc.resolve_template_mappings("generic")}
        for profile in bc.get_supported_profiles():
            with self.subTest(profile=profile):
                dests = {m["destination"] for m in bc.resolve_template_mappings(profile)}
                self.assertEqual(dests, base_dests)

    def test_unknown_profile_raises(self):
        with self.assertRaises(ValueError):
            bc.resolve_template_mappings("unknown-profile")


class TestMarkerParsing(unittest.TestCase):
    """parse_bootstrap_marker() parses the expected fields from a marker file."""

    # Minimal marker table as it appears after apply_bootstrap
    SAMPLE_MARKER = """\
# Bootstrap Source

| Field | Value |
|---|---|
| Bootstrap source repository | https://github.com/incredincomp/agent-bootstrap |
| Bootstrap source version | 0.13.0 |
| Bootstrap source revision | abc123456789 |
| Bootstrap date | 2026-01-01 |
| Agent / operator | apply_bootstrap.py |
| Prompt used | scripts/apply_bootstrap.py |
| Bootstrap profile | python-service |
| Bootstrap notes | N/A |
"""

    def _write_marker(self, tmpdir, content):
        bootstrap_dir = os.path.join(tmpdir, "bootstrap")
        os.makedirs(bootstrap_dir, exist_ok=True)
        path = os.path.join(bootstrap_dir, "BOOTSTRAP_SOURCE.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_marker_not_found(self):
        with tempfile.TemporaryDirectory() as d:
            result = bc.parse_bootstrap_marker(d)
            self.assertFalse(result["found"])

    def test_marker_fields_parsed(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_marker(d, self.SAMPLE_MARKER)
            result = bc.parse_bootstrap_marker(d)
            self.assertTrue(result["found"])
            self.assertEqual(result["version"], "0.13.0")
            self.assertEqual(result["profile"], "python-service")
            self.assertEqual(result["date"], "2026-01-01")
            self.assertEqual(
                result["source_repo"],
                "https://github.com/incredincomp/agent-bootstrap",
            )

    def test_get_bootstrap_marker_path(self):
        path = bc.get_bootstrap_marker_path("/some/repo")
        self.assertEqual(path, "/some/repo/bootstrap/BOOTSTRAP_SOURCE.md")

    def test_unfilled_marker_fields(self):
        unfilled = """\
| Bootstrap source version | {{BOOTSTRAP_SOURCE_VERSION}} |
| Bootstrap profile | {{BOOTSTRAP_PROFILE}} |
"""
        with tempfile.TemporaryDirectory() as d:
            self._write_marker(d, unfilled)
            result = bc.parse_bootstrap_marker(d)
            self.assertTrue(result["found"])
            self.assertEqual(result["version"], "{{BOOTSTRAP_SOURCE_VERSION}}")
            self.assertEqual(result["profile"], "{{BOOTSTRAP_PROFILE}}")


class TestClassifyMarkerEra(unittest.TestCase):
    """classify_marker_era() returns stable, documented era strings."""

    def _marker(self, version=None, profile=None):
        return {"version": version, "profile": profile}

    def test_pre_version_when_no_version(self):
        self.assertEqual(bc.classify_marker_era(self._marker()), "pre-version")

    def test_pre_version_when_version_placeholder(self):
        self.assertEqual(
            bc.classify_marker_era(self._marker(version="{{BOOTSTRAP_SOURCE_VERSION}}")),
            "pre-version",
        )

    def test_pre_profile_when_version_set_but_no_profile(self):
        self.assertEqual(
            bc.classify_marker_era(self._marker(version="0.13.0")),
            "pre-profile",
        )

    def test_pre_profile_when_profile_placeholder(self):
        self.assertEqual(
            bc.classify_marker_era(
                self._marker(version="0.13.0", profile="{{BOOTSTRAP_PROFILE}}")
            ),
            "pre-profile",
        )

    def test_versioned_when_both_set(self):
        self.assertEqual(
            bc.classify_marker_era(self._marker(version="0.13.0", profile="generic")),
            "versioned",
        )

    def test_unknown_when_version_not_semver(self):
        self.assertEqual(
            bc.classify_marker_era(self._marker(version="not-semver", profile="generic")),
            "unknown",
        )


class TestIsPlaceholder(unittest.TestCase):
    """is_placeholder() identifies unfilled {{TOKEN}} values."""

    def test_none_is_not_placeholder(self):
        self.assertFalse(bc.is_placeholder(None))

    def test_exact_token_is_placeholder(self):
        self.assertTrue(bc.is_placeholder("{{REPO_NAME}}"))

    def test_token_with_whitespace_is_placeholder(self):
        self.assertTrue(bc.is_placeholder("  {{REPO_NAME}}  "))

    def test_filled_value_is_not_placeholder(self):
        self.assertFalse(bc.is_placeholder("my-repo-name"))

    def test_partial_token_is_not_placeholder(self):
        self.assertFalse(bc.is_placeholder("{{PARTIAL"))
        self.assertFalse(bc.is_placeholder("PARTIAL}}"))
        self.assertFalse(bc.is_placeholder("text {{TOKEN}} more text"))


class TestHasAndFindPlaceholders(unittest.TestCase):
    """has_placeholders() and find_placeholders() scan text."""

    def test_has_placeholders_true(self):
        self.assertTrue(bc.has_placeholders("Hello {{WORLD}}!"))

    def test_has_placeholders_false(self):
        self.assertFalse(bc.has_placeholders("No tokens here."))

    def test_find_placeholders_returns_all(self):
        found = bc.find_placeholders("{{FOO}} and {{BAR}} and {{FOO}}")
        self.assertEqual(found, ["{{FOO}}", "{{BAR}}", "{{FOO}}"])

    def test_find_placeholders_empty(self):
        self.assertEqual(bc.find_placeholders("nothing here"), [])


class TestSuggestProfileConsistency(unittest.TestCase):
    """
    Cross-script consistency: suggest_profile.py's PROFILES keys must be a
    strict subset of bootstrap_core.PROFILES keys.

    suggest_profile.py intentionally keeps its own PROFILES dict because its
    values are heuristic signal lists, not template overrides — a different data
    shape.  However the profile *names* must stay in sync with bootstrap_core so
    the two tools agree on what profiles exist.

    'generic' is absent from suggest_profile.PROFILES by design: it is the
    "nothing matched" fallback, not a profile with positive heuristic signals.
    """

    def _get_suggest_profile_keys(self):
        """Parse suggest_profile.py's PROFILES dict keys without executing the file."""
        import ast
        suggest_path = os.path.join(_SCRIPTS_DIR, "suggest_profile.py")
        with open(suggest_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "PROFILES"
                and isinstance(node.value, ast.Dict)
            ):
                keys = set()
                for k in node.value.keys:
                    if isinstance(k, ast.Constant):
                        keys.add(k.value)
                return keys
        return set()

    def test_suggest_profile_does_not_import_bootstrap_core(self):
        """suggest_profile.py must not import bootstrap_core (different data shape)."""
        suggest_path = os.path.join(_SCRIPTS_DIR, "suggest_profile.py")
        with open(suggest_path, "r", encoding="utf-8") as f:
            source = f.read()
        self.assertNotIn("bootstrap_core", source,
                         "suggest_profile.py must not import bootstrap_core; "
                         "its PROFILES values are heuristic signals, not template overrides")

    def test_suggest_profile_keys_are_subset_of_core_profiles(self):
        """Every profile in suggest_profile.PROFILES must exist in bootstrap_core.PROFILES."""
        sp_keys = self._get_suggest_profile_keys()
        bc_keys = set(bc.PROFILES.keys())
        unknown = sp_keys - bc_keys
        self.assertEqual(
            unknown, set(),
            f"suggest_profile.py references profiles not in bootstrap_core: {sorted(unknown)}"
        )

    def test_generic_absent_from_suggest_profile(self):
        """'generic' should not appear as a scored profile in suggest_profile.PROFILES."""
        sp_keys = self._get_suggest_profile_keys()
        self.assertNotIn(
            "generic", sp_keys,
            "'generic' must not be a scored profile in suggest_profile.py; "
            "it is the 'nothing matched' fallback"
        )

    def test_non_generic_profiles_all_have_suggest_signals(self):
        """Every non-generic profile in bootstrap_core must be covered by suggest_profile."""
        sp_keys = self._get_suggest_profile_keys()
        bc_non_generic = {k for k in bc.PROFILES if k != "generic"}
        missing = bc_non_generic - sp_keys
        self.assertEqual(
            missing, set(),
            f"Profiles in bootstrap_core but missing from suggest_profile.py: {sorted(missing)}"
        )


if __name__ == "__main__":
    unittest.main()
