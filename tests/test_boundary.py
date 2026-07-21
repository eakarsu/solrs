import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_boundary", ROOT / "scripts" / "verify_boundary.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.boundary = json.loads((ROOT / "BOUNDARY.json").read_text(encoding="utf-8"))

    def test_live_snapshot_is_byte_exact(self):
        result = MODULE.verify(ROOT)
        self.assertEqual(result, {"files": 194, "bytes": 779554, "commits": 272})

    def test_deployable_application_is_rejected(self):
        changed = dict(self.boundary, deployableApplication=True)
        with self.assertRaises(MODULE.BoundaryError):
            MODULE.validate_boundary(changed)

    def test_publish_permission_is_rejected(self):
        changed = dict(self.boundary, prohibitedOperations=["deploy-as-application"])
        with self.assertRaises(MODULE.BoundaryError):
            MODULE.validate_boundary(changed)

    def test_removed_owner_gate_is_rejected(self):
        changed = dict(self.boundary, unresolved=["supported-version"])
        with self.assertRaises(MODULE.BoundaryError):
            MODULE.validate_boundary(changed)

    def test_runtime_and_login_are_not_applicable(self):
        self.assertEqual(self.boundary["runtimeAcceptance"], "not_applicable")
        self.assertEqual(self.boundary["loginAcceptance"], "not_applicable")

    def test_archived_toolchain_is_explicit(self):
        self.assertEqual(self.boundary["archivedToolchain"], {
            "jdk": "8", "sbt": "1.3.3", "scala": ["2.12.8", "2.13.1"], "solr": "7.7.2"
        })

    def test_legacy_release_material_cannot_be_used(self):
        self.assertFalse(self.boundary["legacyReleaseMaterial"]["useAllowed"])

    def test_only_upstream_internal_fixture_symlink_is_retained(self):
        self.assertEqual(self.boundary["retainedSymlink"], {
            "path": "src/test/resources/solr-home/collection2/conf",
            "target": "../collection1/conf/",
            "scope": "internal-test-fixture-only",
        })

    def test_separate_app_requires_complete_boundary(self):
        self.assertEqual(len(self.boundary["applicationExtractionRequires"]), 8)


if __name__ == "__main__":
    unittest.main()
