"""Unit tests for the registry business invariants.

Runs `validate-registry.sh` against fixture registries and asserts on the
exit code and output. No network, stdlib only.
"""

import json
import os
import subprocess
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VALIDATOR = os.path.join(REPO_ROOT, "validate-registry.sh")


def run_validator(registry):
    """Run validate-registry.sh against a registry dict; return (rc, stdout)."""
    with tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False
    ) as f:
        json.dump(registry, f)
        path = f.name
    try:
        result = subprocess.run(
            ["bash", VALIDATOR, path],
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout + result.stderr
    finally:
        os.remove(path)


def base_registry():
    return {
        "name": "test-registry",
        "description": "fixture",
        "version": "1.0.0",
        "generated_at": "2026-08-22",
        "count": 1,
        "skills": [
            {
                "name": "alpha",
                "owner": "someowner",
                "repo": "somerepo",
                "role": "quality",
            }
        ],
    }


class RegistryValidationTests(unittest.TestCase):
    def test_valid_registry(self):
        rc, out = run_validator(base_registry())
        self.assertEqual(rc, 0, out)

    def test_count_mismatch(self):
        reg = base_registry()
        reg["count"] = 99
        rc, out = run_validator(reg)
        self.assertNotEqual(rc, 0)
        self.assertIn("count", out)

    def test_duplicate_skill_name(self):
        reg = base_registry()
        reg["count"] = 2
        reg["skills"].append(dict(reg["skills"][0]))
        reg["skills"][1]["name"] = "alpha"  # same name
        rc, out = run_validator(reg)
        self.assertNotEqual(rc, 0)
        self.assertIn("duplicate skill name", out)

    def test_duplicate_source(self):
        reg = base_registry()
        reg["count"] = 2
        second = dict(reg["skills"][0])
        second["name"] = "beta"  # different name, same source triple-ish
        reg["skills"].append(second)
        # Same (owner, repo, name)? We need a real duplicate source triple.
        second["name"] = reg["skills"][0]["name"]
        rc, out = run_validator(reg)
        self.assertNotEqual(rc, 0)
        self.assertIn("duplicate", out)

    def test_invalid_role(self):
        reg = base_registry()
        reg["skills"][0]["role"] = "bogus"
        rc, out = run_validator(reg)
        self.assertNotEqual(rc, 0)
        self.assertIn("invalid role", out)

    def test_missing_name(self):
        reg = base_registry()
        del reg["skills"][0]["name"]
        rc, out = run_validator(reg)
        self.assertNotEqual(rc, 0)
        self.assertIn("missing 'name'", out)

    def test_missing_owner(self):
        reg = base_registry()
        del reg["skills"][0]["owner"]
        rc, out = run_validator(reg)
        self.assertNotEqual(rc, 0)
        self.assertIn("missing 'owner'", out)

    def test_missing_repo(self):
        reg = base_registry()
        del reg["skills"][0]["repo"]
        rc, out = run_validator(reg)
        self.assertNotEqual(rc, 0)
        self.assertIn("missing 'repo'", out)

    def test_empty_owner(self):
        reg = base_registry()
        reg["skills"][0]["owner"] = ""
        rc, out = run_validator(reg)
        self.assertNotEqual(rc, 0)

    def test_owner_tbd(self):
        reg = base_registry()
        reg["skills"][0]["owner"] = "TBD"
        rc, out = run_validator(reg)
        self.assertNotEqual(rc, 0)
        self.assertIn("TBD", out)

    def test_repo_tbd(self):
        reg = base_registry()
        reg["skills"][0]["repo"] = "TBD"
        rc, out = run_validator(reg)
        self.assertNotEqual(rc, 0)
        self.assertIn("TBD", out)

    def test_unsorted_skills(self):
        reg = base_registry()
        reg["count"] = 2
        reg["skills"] = [
            {"name": "zeta", "owner": "o", "repo": "r", "role": "quality"},
            {"name": "alpha", "owner": "o", "repo": "r", "role": "quality"},
        ]
        rc, out = run_validator(reg)
        self.assertNotEqual(rc, 0)
        self.assertIn("sorted alphabetically", out)

    def test_bad_generated_at(self):
        reg = base_registry()
        reg["generated_at"] = "not-a-date"
        rc, out = run_validator(reg)
        self.assertNotEqual(rc, 0)
        self.assertIn("generated_at", out)


if __name__ == "__main__":
    unittest.main()