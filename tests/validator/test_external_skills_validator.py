"""Mutation tests for scripts/validate-external-skills.py.

These tests intentionally corrupt a COPY of `docs/migration-npx.md` (and
sometimes `external-skills.yaml`) in a `TemporaryDirectory` to verify
that the validator rejects broken migration configurations.

Coverage:
- Missing --global / --copy / --yes flags
- Agent/skill coverage gaps (pair-based: every declared (agent, skill)
  pair must be covered by an install command)
- Second add commands with missing flags
- Variadic --agent / --skill options
- --force in add blocks (rejected)
- --force in prose after a block (not flagged)
- Undeclared sources
- Loop state persistence across commands in the same block
- done resets loop state
- Prose install-count consistency
- Agent coverage from $agent variable, not loop structure alone:
  loop + --agent "$agent" → covers all doc_agents
  loop + --agent claude-code → covers only claude-code
  loop + --agent "$agent" windsurf → rejects windsurf

CRITICAL: NO test in this module ever writes to a real tracked file.
All mutations target copies inside a `TemporaryDirectory`, so an
interrupted test run or parallel execution can never corrupt the
worktree.
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


class _CopyFixture:
    """Context manager: stage a copy of the real doc + yaml in a temp dir.

    The validator reads `docs/migration-npx.md` and `external-skills.yaml`
    from explicit paths now (CLI args or env vars), so we copy the real
    files into a `TemporaryDirectory`, mutate the copies, run the
    validator against the copies, and let the temp dir go out of scope
    on exit. Nothing in the repo is ever modified.
    """

    def __init__(
        self,
        mutated_doc: str | None = None,
        mutated_yaml: str | None = None,
    ) -> None:
        self._mutated_doc = mutated_doc
        self._mutated_yaml = mutated_yaml
        self._tmpdir: tempfile.TemporaryDirectory | None = None
        self.tmpdir: Path | None = None
        self.doc_path: Path | None = None
        self.yaml_path: Path | None = None

    def __enter__(self) -> "_CopyFixture":
        self._tmpdir = tempfile.TemporaryDirectory(prefix="vxt-")
        self.tmpdir = Path(self._tmpdir.name)
        self.doc_path = self.tmpdir / "migration-npx.md"
        self.yaml_path = self.tmpdir / "external-skills.yaml"
        shutil.copy2(MIGRATION_DOC, self.doc_path)
        shutil.copy2(EXTERNAL_YAML, self.yaml_path)
        if self._mutated_doc is not None:
            self.doc_path.write_text(self._mutated_doc, encoding="utf-8")
        if self._mutated_yaml is not None:
            self.yaml_path.write_text(self._mutated_yaml, encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._tmpdir is not None:
            self._tmpdir.cleanup()
            self._tmpdir = None

    def run_validator(self) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["EXTERNAL_SKILLS_MIGRATION_DOC"] = str(self.doc_path)
        env["EXTERNAL_SKILLS_YAML"] = str(self.yaml_path)
        return subprocess.run(
            [sys.executable, str(VALIDATOR)],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            env=env,
            timeout=60,
        )


def _baseline_doc() -> str:
    return MIGRATION_DOC.read_text(encoding="utf-8")


class ValidateExternalSkillsMutationTests(unittest.TestCase):
    """Each test mutates a COPY in a temp dir, runs the validator,
    and asserts on the exit code. The real tracked files are never
    touched."""

    def setUp(self) -> None:
        self._original_doc = _baseline_doc()
        self._original_yaml = EXTERNAL_YAML.read_text(encoding="utf-8")

    # --- Sanity checks ---
    def test_baseline_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=60,
        )
        self.assertEqual(result.returncode, 0)

    def test_baseline_passes_via_env_vars(self) -> None:
        env = os.environ.copy()
        env["EXTERNAL_SKILLS_MIGRATION_DOC"] = str(MIGRATION_DOC)
        env["EXTERNAL_SKILLS_YAML"] = str(EXTERNAL_YAML)
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            env=env,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0)

    def test_baseline_passes_via_cli_args(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(MIGRATION_DOC), str(EXTERNAL_YAML)],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=60,
        )
        self.assertEqual(result.returncode, 0)

    # --- Mode 1: removing --global from an add command must fail. ---
    def test_missing_global_flag_is_rejected(self) -> None:
        mutated = self._original_doc.replace(
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy",
            "npx --yes skills@latest add ksimback/tech-debt-skill --copy",
            1,
        )
        self.assertNotEqual(mutated, self._original_doc)
        with _CopyFixture(mutated_doc=mutated) as fx:
            result = fx.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("--global", result.stdout)

    # --- Mode 2: removing --copy from an add command must fail. ---
    def test_missing_copy_flag_is_rejected(self) -> None:
        mutated = self._original_doc.replace(
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy",
            "npx --yes skills@latest add ksimback/tech-debt-skill --global",
            1,
        )
        self.assertNotEqual(mutated, self._original_doc)
        with _CopyFixture(mutated_doc=mutated) as fx:
            result = fx.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("--copy", result.stdout)

    # --- Mode 2b: removing --yes from an add command must fail. ---
    def test_missing_yes_flag_is_rejected(self) -> None:
        mutated = self._original_doc.replace(
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes",
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit",
            1,
        )
        self.assertNotEqual(mutated, self._original_doc)
        with _CopyFixture(mutated_doc=mutated) as fx:
            result = fx.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("--yes", result.stdout)

    # --- Mode 3: declared agent missing from a non-loop install must fail. ---
    def test_declared_agent_without_install_coverage_is_rejected(self) -> None:
        import yaml

        data = yaml.safe_load(self._original_yaml)
        for src in data.get("sources", []):
            if src.get("name") == "ksimback/tech-debt-skill":
                src["agents"] = ["claude-code", "codex"]
                src["claude_code_only"] = False
        mutated_yaml = yaml.safe_dump(data, sort_keys=False)

        with _CopyFixture(
            mutated_doc=self._original_doc, mutated_yaml=mutated_yaml
        ) as fx:
            result = fx.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertTrue(
            "codex" in result.stdout
            and (
                "no install command" in result.stdout
                or "missing install coverage" in result.stdout
            ),
            msg=result.stdout,
        )

    # --- Mode 4: a second add command in the same block to an
    # undeclared source must be rejected. ---
    def test_second_add_in_block_to_undeclared_source_is_rejected(self) -> None:
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
        with _CopyFixture(mutated_doc=mutated) as fx:
            result = fx.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("undeclared source", result.stdout)
        self.assertIn("undeclared/bogus-source", result.stdout)

    # --- Mode 5: --force inside an add block is rejected. ---
    def test_force_inside_add_block_is_rejected(self) -> None:
        mutated = self._original_doc.replace(
            "  --agent claude-code --skill tech-debt-audit --yes",
            "  --agent claude-code --skill tech-debt-audit --force --yes",
            1,
        )
        self.assertNotEqual(mutated, self._original_doc)
        with _CopyFixture(mutated_doc=mutated) as fx:
            result = fx.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("--force", result.stdout)

    # --- Mode 6: --force in prose right after a fenced block is NOT flagged. ---
    def test_force_in_prose_after_block_is_not_flagged(self) -> None:
        mutated = self._original_doc.replace(
            "## 7. Install i-have-adhd",
            "## 7. Install i-have-adhd\n\n--force is sometimes used in prose examples.",
            1,
        )
        self.assertNotEqual(mutated, self._original_doc)
        with _CopyFixture(mutated_doc=mutated) as fx:
            result = fx.run_validator()
        self.assertEqual(result.returncode, 0)


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
        self.assertFalse(blocks[0].has_agent_loop)
        self.assertFalse(blocks[0].uses_agent_variable)
        self.assertTrue(blocks[0].has_global_flag)
        self.assertTrue(blocks[0].has_copy_flag)
        self.assertTrue(blocks[0].has_yes_flag)

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
        self.assertTrue(blocks[0].has_agent_loop)
        self.assertTrue(
            blocks[0].uses_agent_variable,
            "--agent \"$agent\" inside a for-loop must set uses_agent_variable=True",
        )
        self.assertEqual(blocks[0].literal_agents, [])
        self.assertTrue(blocks[0].has_global_flag)
        self.assertTrue(blocks[0].has_copy_flag)
        self.assertTrue(blocks[0].has_yes_flag)

    def test_block_with_two_distinct_add_commands(self) -> None:
        body = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes\n"
            "npx --yes skills@latest add undeclared/bogus --global --copy \\\n"
            "  --agent claude-code --skill bogus-skill --yes"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].source, "ksimback/tech-debt-skill")
        self.assertEqual(blocks[1].source, "undeclared/bogus")
        for b in blocks:
            self.assertTrue(b.has_global_flag)
            self.assertTrue(b.has_copy_flag)
            self.assertTrue(b.has_yes_flag)

    def test_two_commands_with_distinct_agents_and_skills_no_cross_contamination(
        self,
    ) -> None:
        body = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes\n"
            "npx --yes skills@latest add ayghri/i-have-adhd --global --copy \\\n"
            "  --agent codex --skill i-have-adhd --yes"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].source, "ksimback/tech-debt-skill")
        self.assertEqual(blocks[0].literal_agents, ["claude-code"])
        self.assertEqual(blocks[0].skills, ["tech-debt-audit"])
        self.assertEqual(blocks[1].source, "ayghri/i-have-adhd")
        self.assertEqual(blocks[1].literal_agents, ["codex"])
        self.assertEqual(blocks[1].skills, ["i-have-adhd"])
        for b in blocks:
            self.assertTrue(b.has_global_flag)
            self.assertTrue(b.has_copy_flag)
            self.assertFalse(b.has_agent_loop)

    def test_for_loop_preamble_is_folded_into_command(self) -> None:
        body = (
            "for agent in $AGENTS; do \\\n"
            "  npx --yes skills@latest add obra/superpowers --global --copy \\\n"
            "    --agent \"$agent\" \\\n"
            "    --skill verification-before-completion --yes; \\\n"
            "done"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].source, "obra/superpowers")
        self.assertTrue(blocks[0].has_agent_loop)
        self.assertTrue(blocks[0].uses_agent_variable)
        self.assertEqual(blocks[0].literal_agents, [])

    def test_two_commands_in_same_loop_both_get_uses_agent_loop(self) -> None:
        body = (
            "for agent in $AGENTS; do \\\n"
            "  npx --yes skills@latest add source1/foo --global --copy \\\n"
            "    --agent \"$agent\" --skill a --yes; \\\n"
            "  npx --yes skills@latest add source1/foo --global --copy \\\n"
            "    --agent \"$agent\" --skill b --yes; \\\n"
            "done"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 2)
        for i in (0, 1):
            self.assertEqual(blocks[i].source, "source1/foo")
            self.assertTrue(
                blocks[i].has_agent_loop,
                f"cmd {i}: must report has_agent_loop=True (inside for-loop)",
            )
            self.assertTrue(
                blocks[i].uses_agent_variable,
                f"cmd {i}: must report uses_agent_variable=True ($agent appears in --agent)",
            )
            self.assertEqual(blocks[i].literal_agents, [])
            self.assertEqual(blocks[i].skills, ["a"] if i == 0 else ["b"])

    def test_done_resets_loop_state(self) -> None:
        body = (
            "for agent in $AGENTS; do \\\n"
            "  npx --yes skills@latest add inside/foo --global --copy \\\n"
            "    --agent \"$agent\" --skill a --yes; \\\n"
            "done\n"
            "npx --yes skills@latest add outside/bar --global --copy \\\n"
            "  --agent claude-code --skill b --yes"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].source, "inside/foo")
        self.assertTrue(blocks[0].has_agent_loop)
        self.assertTrue(blocks[0].uses_agent_variable)
        self.assertEqual(blocks[1].source, "outside/bar")
        self.assertFalse(blocks[1].has_agent_loop)
        self.assertFalse(blocks[1].uses_agent_variable)
        self.assertEqual(blocks[1].literal_agents, ["claude-code"])

    def test_split_at_semicolon_within_block(self) -> None:
        body = (
            "npx --yes skills@latest remove --global --agent claude-code "
            "--skill foo --yes; \\\n"
            "npx --yes skills@latest add ksimback/tech-debt-skill "
            "--global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].source, "ksimback/tech-debt-skill")
        self.assertEqual(blocks[0].literal_agents, ["claude-code"])
        self.assertEqual(blocks[0].skills, ["tech-debt-audit"])

    # --- Variadic option tests ---

    def test_variadic_agent_captures_multiple_values(self) -> None:
        body = (
            "npx --yes skills@latest add test/source --global --copy \\\n"
            "  --agent claude-code codex --skill a --yes"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].literal_agents, ["claude-code", "codex"])

    def test_variadic_skill_captures_multiple_values(self) -> None:
        body = (
            "npx --yes skills@latest add test/source --global --copy \\\n"
            "  --agent claude-code --skill a b c --yes"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].skills, ["a", "b", "c"])

    def test_missing_yes_flag_is_detected(self) -> None:
        body = (
            "npx --yes skills@latest add test/source --global --copy \\\n"
            "  --agent claude-code --skill a"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 1)
        self.assertFalse(blocks[0].has_yes_flag)

    # --- Agent variable detection ---

    def test_loop_with_hardcoded_agent_no_variable(self) -> None:
        """Loop with --agent claude-code (not $agent): has_agent_loop=True
        but uses_agent_variable=False. Coverage is only claude-code."""
        body = (
            "for agent in $AGENTS; do \\\n"
            "  npx --yes skills@latest add test/source --global --copy \\\n"
            "    --agent claude-code --skill a --yes; \\\n"
            "done"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 1)
        self.assertTrue(blocks[0].has_agent_loop)
        self.assertFalse(
            blocks[0].uses_agent_variable,
            "hardcoded --agent must not set uses_agent_variable",
        )
        self.assertEqual(blocks[0].literal_agents, ["claude-code"])

    def test_loop_with_agent_variable_and_literal_mixed(self) -> None:
        """--agent "$agent" windsurf: has_agent_loop=True,
        uses_agent_variable=True, literal_agents=['windsurf']."""
        body = (
            "for agent in $AGENTS; do \\\n"
            "  npx --yes skills@latest add test/source --global --copy \\\n"
            "    --agent \"$agent\" windsurf --skill a --yes; \\\n"
            "done"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 1)
        self.assertTrue(blocks[0].has_agent_loop)
        self.assertTrue(blocks[0].uses_agent_variable)
        self.assertEqual(blocks[0].literal_agents, ["windsurf"])

    def test_agent_variable_without_loop(self) -> None:
        """--agent "$agent" without a for-loop: uses_agent_variable=True
        but has_agent_loop=False. The validator must reject this later
        (checked in main, not in parse_add_blocks)."""
        body = (
            "npx --yes skills@latest add test/source --global --copy \\\n"
            '  --agent "$agent" --skill a --yes'
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 1)
        self.assertFalse(blocks[0].has_agent_loop)
        self.assertTrue(
            blocks[0].uses_agent_variable,
            "$agent in --agent must be detected even without a loop",
        )
        self.assertEqual(blocks[0].literal_agents, [])

    def test_literal_before_agent_variable(self) -> None:
        """--agent claude-code "$agent" inside a loop: variable is the
        SECOND value, not immediately after --agent. Must still be
        detected and literal_agents must only contain claude-code."""
        body = (
            "for agent in $AGENTS; do \\\n"
            "  npx --yes skills@latest add test/source --global --copy \\\n"
            '    --agent claude-code "$agent" --skill a --yes; \\\n'
            "done"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 1)
        self.assertTrue(blocks[0].has_agent_loop)
        self.assertTrue(
            blocks[0].uses_agent_variable,
            "$agent as second value after claude-code must be detected",
        )
        self.assertEqual(blocks[0].literal_agents, ["claude-code"])


class ValidateExternalSkillsRegressionTests(unittest.TestCase):
    """End-to-end regression tests for the per-command + pair-based refactor.

    Each test stages a copy of the real files in a `TemporaryDirectory`,
    mutates the copy so the validator sees a specific edge case, runs
    the validator as a subprocess against the copy via the env-var
    API, and asserts on the exit code. The real tracked files are
    never touched.
    """

    def setUp(self) -> None:
        self._original_doc = MIGRATION_DOC.read_text(encoding="utf-8")
        self._original_yaml = EXTERNAL_YAML.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _replace_block(doc: str, new_body: str) -> str:
        old_block = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes"
        )
        new_block = new_body.rstrip()
        new_doc = doc.replace(old_block, new_block, 1)
        assert new_doc != doc, "test setup: ksimback block not found"
        return new_doc

    def _mutate_yaml(self, base_yaml: str, mutate_fn) -> str:
        import yaml

        data = yaml.safe_load(base_yaml)
        mutate_fn(data)
        return yaml.safe_dump(data, sort_keys=False)

    def _set_yaml_source(
        self,
        base_yaml: str,
        name: str,
        *,
        selection: list[str] | None = None,
        agents: list[str] | None = None,
        claude_code_only: bool | None = None,
    ) -> str:
        def mutate(data):
            for src in list(data.get("sources", [])) + list(
                data.get("maintained_locally", [])
            ):
                src_name = src.get("name") or src.get("source")
                if src_name == name:
                    if selection is not None:
                        src["selection"] = list(selection)
                    if agents is not None:
                        src["agents"] = list(agents)
                    if claude_code_only is not None:
                        src["claude_code_only"] = bool(claude_code_only)

        return self._mutate_yaml(base_yaml, mutate)

    def _set_yaml_maintained(
        self,
        base_yaml: str,
        source: str,
        *,
        selection: list[str],
        agents: list[str],
        claude_code_only: bool = False,
    ) -> str:
        def mutate(data):
            loc = data.setdefault("maintained_locally", [])
            for entry in loc:
                if entry.get("source") == source:
                    entry["selection"] = list(selection)
                    entry["agents"] = list(agents)
                    entry["claude_code_only"] = bool(claude_code_only)
                    break
            else:
                loc.append(
                    {
                        "source": source,
                        "selection": list(selection),
                        "agents": list(agents),
                        "verified_commit": None,
                        "verified_at": None,
                        "claude_code_only": bool(claude_code_only),
                        "notes": "test-fixture",
                    }
                )

        return self._mutate_yaml(base_yaml, mutate)

    # ------------------------------------------------------------------
    # Test 1: second add command without --copy is rejected.
    # ------------------------------------------------------------------
    def test_second_command_without_copy_is_rejected(self) -> None:
        mutated_yaml = self._set_yaml_source(
            self._original_yaml,
            "ksimback/tech-debt-skill",
            selection=["tech-debt-audit", "tech-debt-review"],
            agents=["claude-code"],
            claude_code_only=False,
        )
        new_body = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes\n"
            "npx --yes skills@latest add ksimback/tech-debt-skill --global \\\n"
            "  --agent claude-code --skill tech-debt-review --yes"
        )
        mutated_doc = self._replace_block(self._original_doc, new_body)
        with _CopyFixture(mutated_doc=mutated_doc, mutated_yaml=mutated_yaml) as fx:
            result = fx.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("--copy", result.stdout)

    # ------------------------------------------------------------------
    # Test 2: second add command without --global is rejected.
    # ------------------------------------------------------------------
    def test_second_command_without_global_is_rejected(self) -> None:
        mutated_yaml = self._set_yaml_source(
            self._original_yaml,
            "ksimback/tech-debt-skill",
            selection=["tech-debt-audit", "tech-debt-review"],
            agents=["claude-code"],
            claude_code_only=False,
        )
        new_body = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes\n"
            "npx --yes skills@latest add ksimback/tech-debt-skill --copy \\\n"
            "  --agent claude-code --skill tech-debt-review --yes"
        )
        mutated_doc = self._replace_block(self._original_doc, new_body)
        with _CopyFixture(mutated_doc=mutated_doc, mutated_yaml=mutated_yaml) as fx:
            result = fx.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("--global", result.stdout)

    # ------------------------------------------------------------------
    # Test 3: two commands with distinct agents/skills where pairs are
    # not fully covered must be rejected.
    # ------------------------------------------------------------------
    def test_two_commands_missing_pair_coverage_is_rejected(self) -> None:
        mutated_yaml = self._set_yaml_source(
            self._original_yaml,
            "ksimback/tech-debt-skill",
            selection=["tech-debt-audit", "tech-debt-review"],
            agents=["claude-code", "codex"],
            claude_code_only=False,
        )
        mutated_doc = self._original_doc
        mutated_doc = mutated_doc.replace(
            "**33 skills installed for `claude-code`; 32 for `codex`",
            "**34 skills installed for `claude-code`; 34 for `codex`",
            1,
        )
        new_body = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes\n"
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent codex --skill tech-debt-review --yes"
        )
        mutated_doc = self._replace_block(mutated_doc, new_body)
        with _CopyFixture(mutated_doc=mutated_doc, mutated_yaml=mutated_yaml) as fx:
            result = fx.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing install coverage for skills", result.stdout)

    # ------------------------------------------------------------------
    # Test 4: two commands that together cover all pairs pass.
    # ------------------------------------------------------------------
    def test_two_commands_full_pair_coverage_passes(self) -> None:
        mutated_yaml = self._set_yaml_source(
            self._original_yaml,
            "ksimback/tech-debt-skill",
            selection=["tech-debt-audit", "tech-debt-review"],
            agents=["claude-code", "codex", "opencode"],
            claude_code_only=False,
        )
        mutated_doc = self._original_doc
        mutated_doc = mutated_doc.replace(
            "**33 skills installed for `claude-code`; 32 for `codex`",
            "**34 skills installed for `claude-code`; 34 for `codex`",
            1,
        )
        new_body = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --skill tech-debt-review --yes\n"
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent codex --skill tech-debt-audit \\\n"
            "  --agent opencode --skill tech-debt-review --yes"
        )
        mutated_doc = self._replace_block(mutated_doc, new_body)
        with _CopyFixture(mutated_doc=mutated_doc, mutated_yaml=mutated_yaml) as fx:
            result = fx.run_validator()
        self.assertEqual(result.returncode, 0)

    # ------------------------------------------------------------------
    # Test 5: agent missing from the union is rejected.
    # ------------------------------------------------------------------
    def test_agent_missing_from_union_is_rejected(self) -> None:
        mutated_yaml = self._set_yaml_source(
            self._original_yaml,
            "ksimback/tech-debt-skill",
            selection=["tech-debt-audit", "tech-debt-review"],
            agents=["claude-code", "codex", "opencode"],
            claude_code_only=False,
        )
        mutated_doc = self._original_doc
        mutated_doc = mutated_doc.replace(
            "**33 skills installed for `claude-code`; 32 for `codex`",
            "**34 skills installed for `claude-code`; 34 for `codex`",
            1,
        )
        new_body = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes\n"
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent codex --skill tech-debt-review --yes"
        )
        mutated_doc = self._replace_block(mutated_doc, new_body)
        with _CopyFixture(mutated_doc=mutated_doc, mutated_yaml=mutated_yaml) as fx:
            result = fx.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("opencode", result.stdout)
        self.assertTrue(
            "no install command" in result.stdout
            or "missing install coverage" in result.stdout,
            msg=result.stdout,
        )

    # ------------------------------------------------------------------
    # Test 6: local claude-only subtraction from other-agents total.
    # ------------------------------------------------------------------
    def test_local_claude_only_subtracted_from_other_agents_total(self) -> None:
        mutated_yaml = self._set_yaml_maintained(
            self._original_yaml,
            "private-skills",
            selection=["private-claude-only-skill"],
            agents=["claude-code"],
            claude_code_only=True,
        )
        mutated_doc = self._original_doc
        mutated_doc = mutated_doc.replace(
            "**33 skills installed for `claude-code`; 32 for `codex`",
            "**34 skills installed for `claude-code`; 32 for `codex`",
            1,
        )
        install_block = (
            "\n## 9b. Install private-skills (1, claude-only)\n"
            "\n```bash\n"
            "npx --yes skills@latest add private-skills --global --copy \\\n"
            "  --agent claude-code --skill private-claude-only-skill --yes\n"
            "```\n"
        )
        mutated_doc = mutated_doc.replace(
            "## 10. Verify the installation",
            install_block + "## 10. Verify the installation",
            1,
        )
        assert mutated_doc != self._original_doc
        with _CopyFixture(mutated_doc=mutated_doc, mutated_yaml=mutated_yaml) as fx:
            result = fx.run_validator()
        self.assertEqual(result.returncode, 0)
        self.assertIn("32 for `codex`", mutated_doc)
        self.assertIn("34 skills installed for `claude-code`", mutated_doc)

    # ------------------------------------------------------------------
    # Test 7: two add commands inside one for-loop (both use $agent).
    # ------------------------------------------------------------------
    def test_two_add_commands_inside_one_for_loop_passes(self) -> None:
        mutated_yaml = self._set_yaml_source(
            self._original_yaml,
            "ksimback/tech-debt-skill",
            selection=["tech-debt-audit", "tech-debt-review"],
            agents=["claude-code", "codex", "opencode", "cursor"],
            claude_code_only=False,
        )
        mutated_doc = self._original_doc
        mutated_doc = mutated_doc.replace(
            "**33 skills installed for `claude-code`; 32 for `codex`",
            "**34 skills installed for `claude-code`; 34 for `codex`",
            1,
        )
        new_body = (
            "for agent in $AGENTS; do \\\n"
            "  npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "    --agent \"$agent\" --skill tech-debt-audit --yes; \\\n"
            "  npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "    --agent \"$agent\" --skill tech-debt-review --yes; \\\n"
            "done"
        )
        mutated_doc = self._replace_block(mutated_doc, new_body)
        with _CopyFixture(mutated_doc=mutated_doc, mutated_yaml=mutated_yaml) as fx:
            result = fx.run_validator()
        self.assertEqual(result.returncode, 0)

    # ------------------------------------------------------------------
    # Test 8: multiple --force occurrences are all detected.
    # ------------------------------------------------------------------
    def test_multiple_force_flags_are_all_rejected(self) -> None:
        mutated = self._original_doc
        mutated = mutated.replace(
            "  --agent claude-code --skill tech-debt-audit --yes",
            "  --agent claude-code --skill tech-debt-audit --force --yes",
            1,
        )
        mutated = mutated.replace(
            '    --agent "$agent" --skill caveman --yes; \\',
            '    --agent "$agent" --skill caveman --force --yes; \\',
            1,
        )
        self.assertNotEqual(mutated, self._original_doc)
        with _CopyFixture(mutated_doc=mutated) as fx:
            result = fx.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("--force", result.stdout)

    # ------------------------------------------------------------------
    # Test 9: second add command without --yes is rejected.
    # ------------------------------------------------------------------
    def test_second_command_without_yes_is_rejected(self) -> None:
        mutated_yaml = self._set_yaml_source(
            self._original_yaml,
            "ksimback/tech-debt-skill",
            selection=["tech-debt-audit", "tech-debt-review"],
            agents=["claude-code"],
            claude_code_only=False,
        )
        new_body = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes\n"
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-review"
        )
        mutated_doc = self._replace_block(self._original_doc, new_body)
        with _CopyFixture(mutated_doc=mutated_doc, mutated_yaml=mutated_yaml) as fx:
            result = fx.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("--yes", result.stdout)

    # ------------------------------------------------------------------
    # Test 10: REGRESSION — loop with hardcoded --agent claude-code
    # does NOT expand coverage to all $AGENTS. The for-loop is structural
    # only; coverage is determined by what --agent actually receives.
    #
    # The source declares agents [claude-code, codex, opencode].
    # The install block is a for-loop with --agent claude-code (hardcoded).
    # Only claude-code gets coverage → rejected (missing codex, opencode).
    # ------------------------------------------------------------------
    def test_loop_with_hardcoded_agent_incomplete_coverage(self) -> None:
        mutated_yaml = self._set_yaml_source(
            self._original_yaml,
            "ksimback/tech-debt-skill",
            selection=["tech-debt-audit", "tech-debt-review"],
            agents=["claude-code", "codex", "opencode"],
            claude_code_only=False,
        )
        mutated_doc = self._original_doc
        mutated_doc = mutated_doc.replace(
            "**33 skills installed for `claude-code`; 32 for `codex`",
            "**34 skills installed for `claude-code`; 34 for `codex`",
            1,
        )
        new_body = (
            "for agent in $AGENTS; do \\\n"
            "  npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "    --agent claude-code --skill tech-debt-audit --yes; \\\n"
            "done"
        )
        mutated_doc = self._replace_block(mutated_doc, new_body)
        with _CopyFixture(mutated_doc=mutated_doc, mutated_yaml=mutated_yaml) as fx:
            result = fx.run_validator()
        self.assertEqual(
            result.returncode,
            1,
            msg=(
                "loop with hardcoded --agent claude-code must be rejected "
                "(only claude-code covered, codex+opencode missing); "
                f"got exit={result.returncode}\n{result.stdout}"
            ),
        )
        self.assertIn("codex", result.stdout)
        self.assertIn("opencode", result.stdout)

    # ------------------------------------------------------------------
    # Test 11: loop with --agent "$agent" windsurf rejects windsurf
    # (undeclared agent) even though $agent expansion is correct.
    # ------------------------------------------------------------------
    def test_loop_with_agent_variable_and_undeclared_literal_is_rejected(self) -> None:
        mutated_yaml = self._set_yaml_source(
            self._original_yaml,
            "ksimback/tech-debt-skill",
            selection=["tech-debt-audit", "tech-debt-review"],
            agents=["claude-code", "codex", "opencode", "cursor"],
            claude_code_only=False,
        )
        mutated_doc = self._original_doc
        mutated_doc = mutated_doc.replace(
            "**33 skills installed for `claude-code`; 32 for `codex`",
            "**34 skills installed for `claude-code`; 34 for `codex`",
            1,
        )
        new_body = (
            "for agent in $AGENTS; do \\\n"
            "  npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            '    --agent "$agent" windsurf --skill tech-debt-audit --yes; \\\n'
            "done"
        )
        mutated_doc = self._replace_block(mutated_doc, new_body)
        with _CopyFixture(mutated_doc=mutated_doc, mutated_yaml=mutated_yaml) as fx:
            result = fx.run_validator()
        self.assertEqual(
            result.returncode,
            1,
            msg=(
                "loop with --agent '$agent' windsurf must reject windsurf "
                f"(undeclared agent); got exit={result.returncode}\n{result.stdout}"
            ),
        )
        self.assertIn("windsurf", result.stdout)

    # ------------------------------------------------------------------
    # Test 12: mixed $agent + declared literal agents pass when all
    # declared agents are covered.
    # Commands: loop with --agent "$agent" codex → doc_agents ∪ {codex}
    # (codex is already in doc_agents, so it's fine).
    # ------------------------------------------------------------------
    def test_loop_with_agent_variable_and_valid_literal_passes(self) -> None:
        mutated_yaml = self._set_yaml_source(
            self._original_yaml,
            "ksimback/tech-debt-skill",
            selection=["tech-debt-audit", "tech-debt-review"],
            agents=["claude-code", "codex", "opencode", "cursor"],
            claude_code_only=False,
        )
        mutated_doc = self._original_doc
        mutated_doc = mutated_doc.replace(
            "**33 skills installed for `claude-code`; 32 for `codex`",
            "**34 skills installed for `claude-code`; 34 for `codex`",
            1,
        )
        # --agent "$agent" codex: $agent covers all doc_agents, codex is
        # redundant but valid (already in doc_agents). Install both
        # declared skills so all (agent, skill) pairs are covered.
        new_body = (
            "for agent in $AGENTS; do \\\n"
            "  npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            '    --agent "$agent" codex --skill tech-debt-audit --skill tech-debt-review --yes; \\\n'
            "done"
        )
        mutated_doc = self._replace_block(mutated_doc, new_body)
        with _CopyFixture(mutated_doc=mutated_doc, mutated_yaml=mutated_yaml) as fx:
            result = fx.run_validator()
        # All agents are covered (via $agent), so this passes.
        self.assertEqual(
            result.returncode,
            0,
            msg=(
                "loop with --agent '$agent' codex (codex in decl_agents) "
                f"must pass; got exit={result.returncode}\n{result.stdout}"
            ),
        )

    # ------------------------------------------------------------------
    # Test 13: $agent outside a for-loop is rejected.
    #
    # --agent "$agent" without a `for agent in $AGENTS` loop is invalid
    # because the variable would be empty/undefined at runtime. The
    # validator must reject this even though uses_agent_variable=True.
    # ------------------------------------------------------------------
    def test_agent_variable_without_loop_is_rejected(self) -> None:
        mutated_yaml = self._set_yaml_source(
            self._original_yaml,
            "ksimback/tech-debt-skill",
            selection=["tech-debt-audit"],
            agents=["claude-code", "codex", "opencode", "cursor"],
            claude_code_only=False,
        )
        mutated_doc = self._original_doc
        mutated_doc = mutated_doc.replace(
            "**33 skills installed for `claude-code`; 32 for `codex`",
            "**33 skills installed for `claude-code`; 33 for `codex`",
            1,
        )
        # Standalone command with --agent "$agent" — no for-loop anywhere.
        new_body = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            '  --agent "$agent" --skill tech-debt-audit --yes'
        )
        mutated_doc = self._replace_block(mutated_doc, new_body)
        with _CopyFixture(mutated_doc=mutated_doc, mutated_yaml=mutated_yaml) as fx:
            result = fx.run_validator()
        self.assertEqual(
            result.returncode,
            1,
            msg=(
                "$agent without a for-loop must be rejected; "
                f"got exit={result.returncode}\n{result.stdout}"
            ),
        )
        self.assertIn("$agent", result.stdout)
        self.assertIn("not inside", result.stdout)


if __name__ == "__main__":
    unittest.main()
