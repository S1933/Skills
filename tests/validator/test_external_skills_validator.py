"""Tests for validate-external-skills.py.

All mutations target copies in a TemporaryDirectory — real files are
never modified.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
MIGRATION_DOC = ROOT / "docs" / "migration-npx.md"
EXTERNAL_YAML = ROOT / "external-skills.yaml"
VALIDATOR = SCRIPTS / "validate-external-skills.py"


def _load():
    spec = importlib.util.spec_from_file_location("v", VALIDATOR)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, m)
    spec.loader.exec_module(m)
    return m


class Fixture:
    """Stage copies in a temp dir, run validator, assert exit code."""

    def __init__(self, doc: str | None = None, yaml: str | None = None):
        self._doc = doc
        self._yaml = yaml
        self.tmp: Path | None = None
        self.doc_path: Path | None = None
        self.yaml_path: Path | None = None

    def __enter__(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="vxt-"))
        self.doc_path = self.tmp / "migration-npx.md"
        self.yaml_path = self.tmp / "external-skills.yaml"
        shutil.copy2(MIGRATION_DOC, self.doc_path)
        shutil.copy2(EXTERNAL_YAML, self.yaml_path)
        if self._doc is not None:
            self.doc_path.write_text(self._doc, encoding="utf-8")
        if self._yaml is not None:
            self.yaml_path.write_text(self._yaml, encoding="utf-8")
        return self

    def __exit__(self, *a):
        if self.tmp:
            shutil.rmtree(self.tmp)

    def run(self) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["EXTERNAL_SKILLS_MIGRATION_DOC"] = str(self.doc_path)
        env["EXTERNAL_SKILLS_YAML"] = str(self.yaml_path)
        return subprocess.run(
            [sys.executable, str(VALIDATOR)],
            capture_output=True, text=True, cwd=str(ROOT), env=env, timeout=60,
        )


# ── helpers ───────────────────────────────────────────────────────────

def _doc() -> str:
    return MIGRATION_DOC.read_text()

def _yaml() -> str:
    return EXTERNAL_YAML.read_text()

def _mutate_yaml(yaml_text: str, name: str, **kw) -> str:
    import yaml
    data = yaml.safe_load(yaml_text)
    for src in data.get("sources", []) + data.get("maintained_locally", []):
        if (src.get("name") or src.get("source")) == name:
            if "selection" in kw:
                src["selection"] = list(kw["selection"])
            if "agents" in kw:
                src["agents"] = list(kw["agents"])
            if "claude_code_only" in kw:
                src["claude_code_only"] = bool(kw["claude_code_only"])
    return yaml.safe_dump(data, sort_keys=False)

KSIMBACK_BLOCK = (
    "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
    "  --agent claude-code --skill tech-debt-audit --yes"
)

def _replace_block(doc: str, new_body: str) -> str:
    r = doc.replace(KSIMBACK_BLOCK, new_body.rstrip(), 1)
    assert r != doc, "block not found"
    return r


# ── parse-level tests ─────────────────────────────────────────────────

class ParseTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.v = _load()

    def test_literal_command(self):
        body = "npx --yes skills@latest add src/foo --global --copy --agent claude-code --skill a --yes"
        cmds = self.v.parse_cmds(f"```bash\n{body}\n```\n")
        self.assertEqual(len(cmds), 1)
        c = cmds[0]
        self.assertEqual(c.source, "src/foo")
        self.assertEqual(c.agents, ["claude-code"])
        self.assertEqual(c.skills, ["a"])
        self.assertEqual(c.has, {"--global", "--copy", "--yes"})
        self.assertFalse(c.loop)
        self.assertFalse(c.uses_var)

    def test_loop_with_var(self):
        body = (
            "for agent in $AGENTS; do \\\n"
            "  npx --yes skills@latest add src/foo --global --copy \\\n"
            '    --agent "$agent" --skill a --yes; \\\n'
            "done"
        )
        cmds = self.v.parse_cmds(f"```bash\n{body}\n```\n")
        self.assertEqual(len(cmds), 1)
        c = cmds[0]
        self.assertTrue(c.loop)
        self.assertTrue(c.uses_var)
        self.assertEqual(c.agents, [])

    def test_loop_hardcoded_agent(self):
        body = (
            "for agent in $AGENTS; do \\\n"
            "  npx --yes skills@latest add src/foo --global --copy \\\n"
            "    --agent claude-code --skill a --yes; \\\n"
            "done"
        )
        cmds = self.v.parse_cmds(f"```bash\n{body}\n```\n")
        self.assertEqual(len(cmds), 1)
        c = cmds[0]
        self.assertTrue(c.loop)
        self.assertFalse(c.uses_var)
        self.assertEqual(c.agents, ["claude-code"])

    def test_literal_before_var(self):
        body = (
            "for agent in $AGENTS; do \\\n"
            "  npx --yes skills@latest add src/foo --global --copy \\\n"
            '    --agent claude-code "$agent" --skill a --yes; \\\n'
            "done"
        )
        cmds = self.v.parse_cmds(f"```bash\n{body}\n```\n")
        self.assertEqual(len(cmds), 1)
        c = cmds[0]
        self.assertTrue(c.loop)
        self.assertTrue(c.uses_var)
        self.assertEqual(c.agents, ["claude-code"])

    def test_var_without_loop(self):
        body = 'npx --yes skills@latest add src/foo --global --copy --agent "$agent" --skill a --yes'
        cmds = self.v.parse_cmds(f"```bash\n{body}\n```\n")
        self.assertEqual(len(cmds), 1)
        c = cmds[0]
        self.assertFalse(c.loop)
        self.assertTrue(c.uses_var)
        self.assertEqual(c.agents, [])

    def test_variadic_agent(self):
        body = "npx --yes skills@latest add src/foo --global --copy --agent claude-code codex --skill a --yes"
        cmds = self.v.parse_cmds(f"```bash\n{body}\n```\n")
        self.assertEqual(cmds[0].agents, ["claude-code", "codex"])

    def test_variadic_skill(self):
        body = "npx --yes skills@latest add src/foo --global --copy --agent cc --skill a b c --yes"
        cmds = self.v.parse_cmds(f"```bash\n{body}\n```\n")
        self.assertEqual(cmds[0].skills, ["a", "b", "c"])

    def test_missing_yes_detected(self):
        body = "npx --yes skills@latest add src/foo --global --copy --agent cc --skill a"
        cmds = self.v.parse_cmds(f"```bash\n{body}\n```\n")
        self.assertNotIn("--yes", cmds[0].has)

    def test_missing_global_detected(self):
        body = "npx --yes skills@latest add src/foo --copy --agent cc --skill a --yes"
        cmds = self.v.parse_cmds(f"```bash\n{body}\n```\n")
        self.assertNotIn("--global", cmds[0].has)

    def test_missing_copy_detected(self):
        body = "npx --yes skills@latest add src/foo --global --agent cc --skill a --yes"
        cmds = self.v.parse_cmds(f"```bash\n{body}\n```\n")
        self.assertNotIn("--copy", cmds[0].has)


# ── mutation tests ────────────────────────────────────────────────────

class MutationTests(unittest.TestCase):

    def setUp(self):
        self.doc = _doc()
        self.yaml = _yaml()

    def test_baseline(self):
        r = subprocess.run([sys.executable, str(VALIDATOR)], capture_output=True,
                           text=True, cwd=str(ROOT), timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_missing_global(self):
        d = self.doc.replace(
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy",
            "npx --yes skills@latest add ksimback/tech-debt-skill --copy", 1)
        with Fixture(doc=d) as f:
            r = f.run()
        self.assertEqual(r.returncode, 1)
        self.assertIn("--global", r.stdout)

    def test_missing_copy(self):
        d = self.doc.replace(
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy",
            "npx --yes skills@latest add ksimback/tech-debt-skill --global", 1)
        with Fixture(doc=d) as f:
            r = f.run()
        self.assertEqual(r.returncode, 1)
        self.assertIn("--copy", r.stdout)

    def test_missing_yes(self):
        # Remove the skills add --yes (the last one, after --skill).
        old = "  --agent claude-code --skill tech-debt-audit --yes"
        new = "  --agent claude-code --skill tech-debt-audit"
        with Fixture(doc=self.doc.replace(old, new, 1)) as f:
            r = f.run()
        self.assertEqual(r.returncode, 1)
        self.assertIn("--yes", r.stdout)

    def test_force_in_block(self):
        d = self.doc.replace(
            "  --agent claude-code --skill tech-debt-audit --yes",
            "  --agent claude-code --skill tech-debt-audit --force --yes", 1)
        with Fixture(doc=d) as f:
            r = f.run()
        self.assertEqual(r.returncode, 1)
        self.assertIn("--force", r.stdout)

    def test_force_in_prose(self):
        d = self.doc.replace("## 7. Install i-have-adhd",
                             "## 7. Install i-have-adhd\n\n--force example in prose.")
        with Fixture(doc=d) as f:
            r = f.run()
        self.assertEqual(r.returncode, 0)

    def test_undeclared_source(self):
        new = "npx --yes skills@latest add bogus/x --global --copy --agent cc --skill s --yes"
        with Fixture(doc=self.doc.replace(KSIMBACK_BLOCK, new, 1)) as f:
            r = f.run()
        self.assertEqual(r.returncode, 1)
        self.assertIn("undeclared", r.stdout)

    def test_missing_agent_coverage(self):
        y = _mutate_yaml(self.yaml, "ksimback/tech-debt-skill",
                         agents=["claude-code", "codex"], claude_code_only=False)
        with Fixture(doc=self.doc, yaml=y) as f:
            r = f.run()
        self.assertEqual(r.returncode, 1)
        self.assertIn("codex", r.stdout)

    # ── pair-based coverage ────────────────────────────────────────

    def test_missing_pair_coverage(self):
        y = _mutate_yaml(self.yaml, "ksimback/tech-debt-skill",
                         selection=["tech-debt-audit", "tech-debt-review"],
                         agents=["claude-code", "codex"], claude_code_only=False)
        d = self.doc.replace(
            "**33 skills installed for `claude-code`; 32 for `codex`",
            "**34 skills installed for `claude-code`; 34 for `codex`", 1)
        new_body = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes\n"
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent codex --skill tech-debt-review --yes"
        )
        d = _replace_block(d, new_body)
        with Fixture(doc=d, yaml=y) as f:
            r = f.run()
        self.assertEqual(r.returncode, 1)
        self.assertIn("missing skills", r.stdout)

    def test_full_pair_coverage(self):
        y = _mutate_yaml(self.yaml, "ksimback/tech-debt-skill",
                         selection=["tech-debt-audit", "tech-debt-review"],
                         agents=["claude-code", "codex", "opencode"],
                         claude_code_only=False)
        d = self.doc.replace(
            "**33 skills installed for `claude-code`; 32 for `codex`",
            "**34 skills installed for `claude-code`; 34 for `codex`", 1)
        new_body = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --skill tech-debt-review --yes\n"
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent codex --skill tech-debt-audit \\\n"
            "  --agent opencode --skill tech-debt-review --yes"
        )
        d = _replace_block(d, new_body)
        with Fixture(doc=d, yaml=y) as f:
            r = f.run()
        self.assertEqual(r.returncode, 0)

    # ── loop/var semantics ─────────────────────────────────────────

    def test_var_without_loop_rejected(self):
        y = _mutate_yaml(self.yaml, "ksimback/tech-debt-skill",
                         selection=["tech-debt-audit"], agents=["claude-code"],
                         claude_code_only=False)
        new_body = 'npx --yes skills@latest add ksimback/tech-debt-skill --global --copy --agent "$agent" --skill tech-debt-audit --yes'
        with Fixture(doc=_replace_block(self.doc, new_body), yaml=y) as f:
            r = f.run()
        self.assertEqual(r.returncode, 1)
        self.assertIn("$agent", r.stdout)
        self.assertIn("no for loop", r.stdout)

    def test_loop_hardcoded_agent_no_expand(self):
        y = _mutate_yaml(self.yaml, "ksimback/tech-debt-skill",
                         selection=["tech-debt-audit"],
                         agents=["claude-code", "codex", "opencode"],
                         claude_code_only=False)
        d = self.doc.replace(
            "**33 skills installed for `claude-code`; 32 for `codex`",
            "**33 skills installed for `claude-code`; 33 for `codex`", 1)
        new_body = (
            "for agent in $AGENTS; do \\\n"
            "  npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "    --agent claude-code --skill tech-debt-audit --yes; \\\n"
            "done"
        )
        d = _replace_block(d, new_body)
        with Fixture(doc=d, yaml=y) as f:
            r = f.run()
        self.assertEqual(r.returncode, 1)
        self.assertIn("codex", r.stdout)

    def test_loop_var_undeclared_literal_rejected(self):
        y = _mutate_yaml(self.yaml, "ksimback/tech-debt-skill",
                         selection=["tech-debt-audit"],
                         agents=["claude-code", "codex", "opencode", "cursor"],
                         claude_code_only=False)
        d = self.doc.replace(
            "**33 skills installed for `claude-code`; 32 for `codex`",
            "**33 skills installed for `claude-code`; 33 for `codex`", 1)
        new_body = (
            "for agent in $AGENTS; do \\\n"
            "  npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            '    --agent "$agent" windsurf --skill tech-debt-audit --yes; \\\n'
            "done"
        )
        d = _replace_block(d, new_body)
        with Fixture(doc=d, yaml=y) as f:
            r = f.run()
        self.assertEqual(r.returncode, 1)
        self.assertIn("windsurf", r.stdout)

    def test_loop_two_cmds_passes(self):
        y = _mutate_yaml(self.yaml, "ksimback/tech-debt-skill",
                         selection=["tech-debt-audit", "tech-debt-review"],
                         agents=["claude-code", "codex", "opencode", "cursor"],
                         claude_code_only=False)
        d = self.doc.replace(
            "**33 skills installed for `claude-code`; 32 for `codex`",
            "**34 skills installed for `claude-code`; 34 for `codex`", 1)
        new_body = (
            "for agent in $AGENTS; do \\\n"
            "  npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            '    --agent "$agent" --skill tech-debt-audit --yes; \\\n'
            "  npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            '    --agent "$agent" --skill tech-debt-review --yes; \\\n'
            "done"
        )
        d = _replace_block(d, new_body)
        with Fixture(doc=d, yaml=y) as f:
            r = f.run()
        self.assertEqual(r.returncode, 0, r.stdout)

    # ── other ───────────────────────────────────────────────────────

    def test_multiple_force(self):
        d = self.doc
        d = d.replace("  --agent claude-code --skill tech-debt-audit --yes",
                       "  --agent claude-code --skill tech-debt-audit --force --yes", 1)
        d = d.replace('    --agent "$agent" --skill caveman --yes; \\',
                       '    --agent "$agent" --skill caveman --force --yes; \\', 1)
        with Fixture(doc=d) as f:
            r = f.run()
        self.assertEqual(r.returncode, 1)
        self.assertIn("--force", r.stdout)

    def test_local_claude_only_subtraction(self):
        y = self.yaml
        import yaml as yml
        data = yml.safe_load(y)
        data.setdefault("maintained_locally", []).append(dict(
            source="private-skills", selection=["priv"], agents=["claude-code"],
            claude_code_only=True, verified_commit=None, verified_at=None, notes=""))
        y = yml.safe_dump(data, sort_keys=False)
        d = self.doc.replace(
            "**33 skills installed for `claude-code`; 32 for `codex`",
            "**34 skills installed for `claude-code`; 32 for `codex`", 1)
        d = d.replace("## 10. Verify", (
            "\n## 9b. Private\n\n```bash\n"
            "npx --yes skills@latest add private-skills --global --copy \\\n"
            "  --agent claude-code --skill priv --yes\n```\n\n## 10. Verify"), 1)
        with Fixture(doc=d, yaml=y) as f:
            r = f.run()
        self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    unittest.main()
