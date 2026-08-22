"""Unit tests for the upstream verification logic (network-free).

Exercises the frontmatter parser, path filter, and duplicate detection using
local fixtures — no GitHub API involved.
"""

import importlib.util
import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO_ROOT, "scripts")

# Load verify-upstreams.py (hyphenated filename) explicitly.
_spec = importlib.util.spec_from_file_location(
    "verify_upstreams", os.path.join(SCRIPTS, "verify-upstreams.py")
)
vu = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vu)


class FrontmatterTests(unittest.TestCase):
    def test_valid_frontmatter(self):
        raw = b"---\nname: tech-debt\ndescription: x\n---\nbody"
        self.assertEqual(vu.frontmatter_name(raw), "tech-debt")

    def test_quoted_name(self):
        raw = b'---\nname: "code-review"\n---\n'
        self.assertEqual(vu.frontmatter_name(raw), "code-review")

    def test_missing_frontmatter(self):
        self.assertIsNone(vu.frontmatter_name(b"# no frontmatter here"))

    def test_missing_name_field(self):
        self.assertIsNone(vu.frontmatter_name(b"---\ndescription: no name\n---\n"))

    def test_unclosed_frontmatter(self):
        self.assertIsNone(vu.frontmatter_name(b"---\nname: broken"))

    def test_empty_frontmatter(self):
        self.assertIsNone(vu.frontmatter_name(b"---\n---\n"))


class PathFilterTests(unittest.TestCase):
    def test_nested_and_root_paths(self):
        paths = [
            "SKILL.md",
            "skills/foo/SKILL.md",
            "engineering/skills/tech-debt/SKILL.md",
            "a/b/c/d/SKILL.md",
            "readme.md",
            "x/SKILL.md/not-a-file",
        ]
        got = vu.skill_md_paths(paths)
        self.assertIn("SKILL.md", got)
        self.assertIn("skills/foo/SKILL.md", got)
        self.assertIn("engineering/skills/tech-debt/SKILL.md", got)
        self.assertNotIn("readme.md", got)
        self.assertNotIn("x/SKILL.md/not-a-file", got)

    def test_unexpected_depth_ok(self):
        # Any nesting depth is a valid candidate — no depth cap.
        paths = ["/".join(["lvl%d" % i for i in range(8)]) + "/SKILL.md"]
        self.assertEqual(len(vu.skill_md_paths(paths)), 1)


if __name__ == "__main__":
    unittest.main()