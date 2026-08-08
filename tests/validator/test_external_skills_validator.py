"""Mutation tests for scripts/validate-external-skills.py.

These tests intentionally corrupt `docs/migration-npx.md` to verify that
the validator rejects four classes of broken migration configuration
that a prior review of the validator found it accepted by accident:

1. Removing `--global` from an `npx skills add` command.
2. Removing `--copy` from an `npx skills add` command.
3. A source declared for several agents (e.g. claude-code AND codex),
   but the install block only uses `--agent claude-code` (missing agent
   coverage).
4. A single fenced ```` ```bash ```` block containing two `npx skills
   add` commands where the second targets an undeclared source — the
   prior parser only saw the first command and silently passed.

The tests temporarily rewrite the migration doc, run the validator
script as a subprocess, assert exit code 1, then restore the doc.
This is the most faithful way to exercise the validator (it covers the
script's `main()` and CLI exit code, not just the helpers).
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
MIGRATION_DOC = ROOT / "docs" / "migration-npx.md"
VALIDATOR = SCRIPTS / "validate-external-skills.py"


def _load_validator():
    """Import the validator module so we can inspect parsed structures."""
    spec = importlib.util.spec_from_file_location(
        "validate_external_skills", VALIDATOR
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


class _DocRewriter:
    """Context manager: write a mutated doc, run validator, restore.

    The validator reads `docs/migration-npx.md` from its own `ROOT` so
    we rewrite the real file in place and restore it in `__exit__`. We
    also restore it defensively on exception.
    """

    def __init__(self, mutated_text: str) -> None:
        self.mutated_text = mutated_text
        self._backup: str | None = None

    def __enter__(self) -> "_DocRewriter":
        self._backup = MIGRATION_DOC.read_text(encoding="utf-8")
        MIGRATION_DOC.write_text(self.mutated_text, encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._backup is not None:
            MIGRATION_DOC.write_text(self._backup, encoding="utf-8")
            self._backup = None

    def run_validator(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(VALIDATOR)],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=60,
        )


def _baseline_doc() -> str:
    return MIGRATION_DOC.read_text(encoding="utf-8")


class ValidateExternalSkillsMutationTests(unittest.TestCase):
    """Each test mutates the doc, runs the validator, and asserts exit=1.

    The doc is restored in `setUp`/`tearDown` as a belt-and-braces guard
    around the context manager used in each test.
    """

    def setUp(self) -> None:
        self._original_doc = _baseline_doc()
        self._original_validator = _load_validator()

    def tearDown(self) -> None:
        # Always restore the doc on the way out, even if a test failed
        # before the context manager's `__exit__` ran.
        MIGRATION_DOC.write_text(self._original_doc, encoding="utf-8")

    # --- Sanity check: the baseline must still validate. ---
    def test_baseline_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=60,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=(
                f"baseline validator must pass; got exit={result.returncode}\n"
                f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            ),
        )

    # --- Mode 1: removing --global from an add command must fail. ---
    def test_missing_global_flag_is_rejected(self) -> None:
        mutated = self._original_doc.replace(
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy",
            "npx --yes skills@latest add ksimback/tech-debt-skill --copy",
            1,
        )
        self.assertNotEqual(mutated, self._original_doc, "test setup: no replacement made")
        with _DocRewriter(mutated) as rw:
            result = rw.run_validator()
        self.assertEqual(
            result.returncode,
            1,
            msg=f"missing --global must be rejected; got {result.returncode}\n{result.stdout}",
        )
        self.assertIn("--global", result.stdout)

    # --- Mode 2: removing --copy from an add command must fail. ---
    def test_missing_copy_flag_is_rejected(self) -> None:
        mutated = self._original_doc.replace(
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy",
            "npx --yes skills@latest add ksimback/tech-debt-skill --global",
            1,
        )
        self.assertNotEqual(mutated, self._original_doc)
        with _DocRewriter(mutated) as rw:
            result = rw.run_validator()
        self.assertEqual(
            result.returncode,
            1,
            msg=f"missing --copy must be rejected; got {result.returncode}\n{result.stdout}",
        )
        self.assertIn("--copy", result.stdout)

    # --- Mode 3: declared agent missing from a non-loop install must fail. ---
    def test_declared_agent_without_install_coverage_is_rejected(self) -> None:
        # Take the ksimback block (which already installs for claude-code)
        # and add a SECOND add command inside the same fenced block that
        # installs only for codex. We also need to extend the YAML
        # declaration so that ksimback now claims agents=[claude-code,
        # codex]. The validator should reject the doc as soon as it sees
        # that no install block covers codex.
        import yaml

        yaml_path = ROOT / "external-skills.yaml"
        original_yaml = yaml_path.read_text(encoding="utf-8")
        data = yaml.safe_load(original_yaml)
        for src in data.get("sources", []):
            if src.get("name") == "ksimback/tech-debt-skill":
                src["agents"] = ["claude-code", "codex"]
                src["claude_code_only"] = False
        mutated_yaml = yaml.safe_dump(data, sort_keys=False)
        yaml_path.write_text(mutated_yaml, encoding="utf-8")

        try:
            # The single existing install block for ksimback only
            # covers --agent claude-code. No loop, no second add command
            # for codex, so codex has no install coverage.
            with _DocRewriter(self._original_doc) as rw:
                result = rw.run_validator()
            self.assertEqual(
                result.returncode,
                1,
                msg=(
                    "missing agent coverage for codex must be rejected; "
                    f"got exit={result.returncode}\n{result.stdout}"
                ),
            )
            # Should mention the missing agent (codex) and/or the union
            # coverage check.
            self.assertTrue(
                "codex" in result.stdout
                and (
                    "missing coverage" in result.stdout
                    or "no install block installs on them" in result.stdout
                ),
                msg=result.stdout,
            )
        finally:
            yaml_path.write_text(original_yaml, encoding="utf-8")

    # --- Mode 4: a second add command in the same block to an
    # undeclared source must be rejected. ---
    def test_second_add_in_block_to_undeclared_source_is_rejected(self) -> None:
        # Append a second `npx skills add` line inside the existing
        # ksimback fenced block. The first command targets a declared
        # source; the second targets an undeclared one. The old parser
        # only saw the first command, so the bug went unnoticed.
        old_block = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes"
        )
        new_block = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes\n"
            "npx --yes skills@latest add undeclared/bogus-source --global --copy \\\n"
            "  --agent claude-code --skill bogus-skill --yes"
        )
        mutated = self._original_doc.replace(old_block, new_block, 1)
        self.assertNotEqual(mutated, self._original_doc)
        with _DocRewriter(mutated) as rw:
            result = rw.run_validator()
        self.assertEqual(
            result.returncode,
            1,
            msg=(
                "undeclared source in second add command must be rejected; "
                f"got exit={result.returncode}\n{result.stdout}"
            ),
        )
        self.assertIn("undeclared source", result.stdout)
        self.assertIn("undeclared/bogus-source", result.stdout)


class ParseAddBlocksTests(unittest.TestCase):
    """Unit-level checks for the multi-command splitter.

    These do not require touching the on-disk doc.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = _load_validator()

    def test_single_command_block(self) -> None:
        body = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].source, "ksimback/tech-debt-skill")
        self.assertEqual(blocks[0].literal_agents, ["claude-code"])
        self.assertTrue(blocks[0].has_global_flag)
        self.assertTrue(blocks[0].has_copy_flag)

    def test_loop_block_keeps_loop_marker(self) -> None:
        body = (
            "for agent in $AGENTS; do \\\n"
            "  npx --yes skills@latest add obra/superpowers --global --copy \\\n"
            "    --agent \"$agent\" \\\n"
            "    --skill verification-before-completion --yes; \\\n"
            "done"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 1)
        self.assertTrue(blocks[0].uses_agent_loop)
        # The loop's `--agent "$agent"` does not count as a literal
        # agent; the source's declared agent set is checked against
        # $AGENTS instead.
        self.assertEqual(blocks[0].literal_agents, [])
        self.assertTrue(blocks[0].has_global_flag)
        self.assertTrue(blocks[0].has_copy_flag)

    def test_block_with_two_distinct_add_commands(self) -> None:
        body = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes\n"
            "npx --yes skills@latest add undeclared/bogus --global --copy \\\n"
            "  --agent claude-code --skill bogus-skill --yes"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 2, f"expected 2 AddBlocks, got {len(blocks)}")
        self.assertEqual(blocks[0].source, "ksimback/tech-debt-skill")
        self.assertEqual(blocks[1].source, "undeclared/bogus")
        for b in blocks:
            self.assertTrue(b.has_global_flag)
            self.assertTrue(b.has_copy_flag)


if __name__ == "__main__":
    unittest.main()
