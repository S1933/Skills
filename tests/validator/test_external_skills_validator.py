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
        # Start from the real tracked files; mutations only affect copies.
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
        """Run the validator against the copies via the env-var API.

        The env-var route keeps the CLI test surface minimal — there's
        no need to pass positional args through subprocess when the env
        var does the job.
        """
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

    # --- Sanity check: the baseline (real files) must still validate. ---
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

    # --- Sanity check: the same baseline via env vars passes too. ---
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
        self.assertEqual(
            result.returncode,
            0,
            msg=(
                f"baseline via env vars must pass; got exit={result.returncode}\n"
                f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            ),
        )

    # --- Sanity check: the same baseline via CLI args passes too. ---
    def test_baseline_passes_via_cli_args(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(MIGRATION_DOC), str(EXTERNAL_YAML)],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=60,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=(
                f"baseline via CLI args must pass; got exit={result.returncode}\n"
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
        with _CopyFixture(mutated_doc=mutated) as fx:
            result = fx.run_validator()
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
        with _CopyFixture(mutated_doc=mutated) as fx:
            result = fx.run_validator()
        self.assertEqual(
            result.returncode,
            1,
            msg=f"missing --copy must be rejected; got {result.returncode}\n{result.stdout}",
        )
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
        self.assertEqual(
            result.returncode,
            1,
            msg=f"missing --yes must be rejected; got {result.returncode}\n{result.stdout}",
        )
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
        self.assertEqual(
            result.returncode,
            1,
            msg=(
                "missing agent coverage for codex must be rejected; "
                f"got exit={result.returncode}\n{result.stdout}"
            ),
        )
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
        self.assertEqual(
            result.returncode,
            1,
            msg=f"--force in add block must be rejected; got {result.returncode}\n{result.stdout}",
        )
        self.assertIn("--force", result.stdout)

    # --- Mode 6: --force in prose right after a fenced block is NOT
    # flagged (it's outside the add block's span). ---
    def test_force_in_prose_after_block_is_not_flagged(self) -> None:
        # The ksimback install block is followed by "## 7. Install i-have-adhd".
        # Insert --force in that prose section (between the ``` closing fence
        # and the next heading).
        mutated = self._original_doc.replace(
            "## 7. Install i-have-adhd",
            "## 7. Install i-have-adhd\n\n--force is sometimes used in prose examples.",
            1,
        )
        self.assertNotEqual(mutated, self._original_doc)
        with _CopyFixture(mutated_doc=mutated) as fx:
            result = fx.run_validator()
        self.assertEqual(
            result.returncode,
            0,
            msg=f"--force in prose must not be flagged; got {result.returncode}\n{result.stdout}",
        )


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
        self.assertTrue(blocks[0].uses_agent_loop)
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
        self.assertEqual(len(blocks), 2, f"expected 2 AddBlocks, got {len(blocks)}")
        self.assertEqual(blocks[0].source, "ksimback/tech-debt-skill")
        self.assertEqual(blocks[1].source, "undeclared/bogus")
        for b in blocks:
            self.assertTrue(b.has_global_flag)
            self.assertTrue(b.has_copy_flag)
            self.assertTrue(b.has_yes_flag)

    def test_two_commands_with_distinct_agents_and_skills_no_cross_contamination(
        self,
    ) -> None:
        """Per-command parser must NOT bleed flags/agents/skills between commands."""
        body = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes\n"
            "npx --yes skills@latest add ayghri/i-have-adhd --global --copy \\\n"
            "  --agent codex --skill i-have-adhd --yes"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 2, f"expected 2 AddBlocks, got {len(blocks)}")
        self.assertEqual(blocks[0].source, "ksimback/tech-debt-skill")
        self.assertEqual(blocks[0].literal_agents, ["claude-code"])
        self.assertEqual(blocks[0].skills, ["tech-debt-audit"])
        self.assertEqual(blocks[1].source, "ayghri/i-have-adhd")
        self.assertEqual(blocks[1].literal_agents, ["codex"])
        self.assertEqual(blocks[1].skills, ["i-have-adhd"])
        for b in blocks:
            self.assertTrue(b.has_global_flag)
            self.assertTrue(b.has_copy_flag)
            self.assertFalse(b.uses_agent_loop)

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
        self.assertTrue(blocks[0].uses_agent_loop)
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
        self.assertEqual(len(blocks), 2, f"expected 2 AddBlocks, got {len(blocks)}")
        self.assertEqual(blocks[0].source, "source1/foo")
        self.assertEqual(blocks[0].skills, ["a"])
        self.assertTrue(blocks[0].uses_agent_loop)
        self.assertEqual(blocks[1].source, "source1/foo")
        self.assertEqual(blocks[1].skills, ["b"])
        self.assertTrue(blocks[1].uses_agent_loop)
        self.assertEqual(blocks[0].literal_agents, [])
        self.assertEqual(blocks[1].literal_agents, [])

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
        self.assertEqual(len(blocks), 2, f"expected 2 AddBlocks, got {len(blocks)}")
        self.assertEqual(blocks[0].source, "inside/foo")
        self.assertTrue(blocks[0].uses_agent_loop)
        self.assertEqual(blocks[1].source, "outside/bar")
        self.assertFalse(blocks[1].uses_agent_loop)
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
        self.assertEqual(len(blocks), 1, f"expected 1 AddBlock, got {len(blocks)}")
        self.assertEqual(blocks[0].source, "ksimback/tech-debt-skill")
        self.assertEqual(blocks[0].literal_agents, ["claude-code"])
        self.assertEqual(blocks[0].skills, ["tech-debt-audit"])

    # --- Variadic option tests ---

    def test_variadic_agent_captures_multiple_values(self) -> None:
        """--agent claude-code codex must capture both values."""
        body = (
            "npx --yes skills@latest add test/source --global --copy \\\n"
            "  --agent claude-code codex --skill a --yes"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].literal_agents, ["claude-code", "codex"])

    def test_variadic_skill_captures_multiple_values(self) -> None:
        """--skill a b c must capture all three values."""
        body = (
            "npx --yes skills@latest add test/source --global --copy \\\n"
            "  --agent claude-code --skill a b c --yes"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].skills, ["a", "b", "c"])

    def test_missing_yes_flag_is_detected(self) -> None:
        """An add command without the final --yes must have has_yes_flag=False."""
        body = (
            "npx --yes skills@latest add test/source --global --copy \\\n"
            "  --agent claude-code --skill a"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 1)
        self.assertFalse(blocks[0].has_yes_flag)


class ValidateExternalSkillsRegressionTests(unittest.TestCase):
    """End-to-end regression tests for the per-command + pair-based refactor.

    Each test stages a copy of the real files in a `TemporaryDirectory`,
    mutates the copy so the validator sees a specific edge case, runs
    the validator as a subprocess against the copy via the env-var
    API, and asserts on the exit code. The real tracked files are
    never touched. These tests are the safety net against the
    cross-contamination bug and the missing pair-coverage check.
    """

    def setUp(self) -> None:
        self._original_doc = MIGRATION_DOC.read_text(encoding="utf-8")
        self._original_yaml = EXTERNAL_YAML.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Helpers for swapping out a fenced block and the YAML declaration.
    # All helpers only operate on the COPY in the active `_CopyFixture`
    # — they never write to the real repo files.
    # ------------------------------------------------------------------
    @staticmethod
    def _replace_block(doc: str, new_body: str) -> str:
        r"""Replace the fenced block whose body matches the ksimback single
        install with `new_body`. The body is wrapped in a ```bash ... ```
        fence. Returns the rewritten doc."""
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
    # Test 1: a SECOND add command without --copy is rejected.
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
            # Second command: missing --copy.
            "npx --yes skills@latest add ksimback/tech-debt-skill --global \\\n"
            "  --agent claude-code --skill tech-debt-review --yes"
        )
        mutated_doc = self._replace_block(self._original_doc, new_body)
        with _CopyFixture(
            mutated_doc=mutated_doc, mutated_yaml=mutated_yaml
        ) as fx:
            result = fx.run_validator()
        self.assertEqual(
            result.returncode,
            1,
            msg=(
                "second add command missing --copy must be rejected; "
                f"got exit={result.returncode}\n{result.stdout}"
            ),
        )
        self.assertIn("--copy", result.stdout)

    # ------------------------------------------------------------------
    # Test 2: a SECOND add command without --global is rejected.
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
            # Second command: missing --global.
            "npx --yes skills@latest add ksimback/tech-debt-skill --copy \\\n"
            "  --agent claude-code --skill tech-debt-review --yes"
        )
        mutated_doc = self._replace_block(self._original_doc, new_body)
        with _CopyFixture(
            mutated_doc=mutated_doc, mutated_yaml=mutated_yaml
        ) as fx:
            result = fx.run_validator()
        self.assertEqual(
            result.returncode,
            1,
            msg=(
                "second add command missing --global must be rejected; "
                f"got exit={result.returncode}\n{result.stdout}"
            ),
        )
        self.assertIn("--global", result.stdout)

    # ------------------------------------------------------------------
    # Test 3: two commands with distinct agents and skills where not all
    # (agent, skill) pairs are covered must be REJECTED.
    #
    # Command 1: --agent claude-code --skill tech-debt-audit
    # Command 2: --agent codex --skill tech-debt-review
    # Declaration: agents=[claude-code, codex], skills=[audit, review]
    #
    # Covered pairs: {(claude-code, audit), (codex, review)}
    # Expected pairs: {(claude-code, audit), (claude-code, review),
    #                  (codex, audit), (codex, review)}
    # Missing: {(claude-code, review), (codex, audit)} → rejected.
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
        with _CopyFixture(
            mutated_doc=mutated_doc, mutated_yaml=mutated_yaml
        ) as fx:
            result = fx.run_validator()
        self.assertEqual(
            result.returncode,
            1,
            msg=(
                "two commands with non-covering (agent, skill) pairs must "
                f"be rejected; got exit={result.returncode}\n{result.stdout}\n"
                f"STDERR: {result.stderr}"
            ),
        )
        self.assertIn("missing install coverage for skills", result.stdout)

    # ------------------------------------------------------------------
    # Test 4: two literal commands that together cover all (agent, skill)
    # pairs are accepted.
    #
    # Command 1: claude-code gets BOTH skills.
    # Command 2: codex+opencode get BOTH skills (via variadic --agent
    # and interleaved --agent/--skill flags).
    # All pairs: {(claude-code, audit), (claude-code, review),
    #             (codex, audit), (codex, review),
    #             (opencode, audit), (opencode, review)} ✓
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
            # First command: covers both skills for claude-code.
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --skill tech-debt-review --yes\n"
            # Second command: covers both skills for codex AND opencode.
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent codex --skill tech-debt-audit \\\n"
            "  --agent opencode --skill tech-debt-review --yes"
        )
        mutated_doc = self._replace_block(mutated_doc, new_body)
        with _CopyFixture(
            mutated_doc=mutated_doc, mutated_yaml=mutated_yaml
        ) as fx:
            result = fx.run_validator()
        self.assertEqual(
            result.returncode,
            0,
            msg=(
                "full pair coverage must pass; "
                f"got exit={result.returncode}\n{result.stdout}\n"
                f"STDERR: {result.stderr}"
            ),
        )

    # ------------------------------------------------------------------
    # Test 5: an agent missing from the UNION is rejected.
    #
    # The source declares three agents; the doc only has two commands
    # covering two of them. The union {claude-code, codex} is missing
    # `opencode`, so the validator must reject.
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
        with _CopyFixture(
            mutated_doc=mutated_doc, mutated_yaml=mutated_yaml
        ) as fx:
            result = fx.run_validator()
        self.assertEqual(
            result.returncode,
            1,
            msg=(
                "agent missing from union must be rejected; "
                f"got exit={result.returncode}\n{result.stdout}"
            ),
        )
        self.assertIn("opencode", result.stdout)
        self.assertTrue(
            "no install command" in result.stdout
            or "missing install coverage" in result.stdout,
            msg=result.stdout,
        )

    # ------------------------------------------------------------------
    # Test 6: a local Claude-only selection is subtracted from the
    # other-agents total (Change C regression).
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
        assert mutated_doc != self._original_doc, "test setup: injection failed"
        with _CopyFixture(
            mutated_doc=mutated_doc, mutated_yaml=mutated_yaml
        ) as fx:
            result = fx.run_validator()
        self.assertEqual(
            result.returncode,
            0,
            msg=(
                "local claude-only skill must be subtracted from other-agents "
                f"prose count; got exit={result.returncode}\n{result.stdout}\n"
                f"STDERR: {result.stderr}"
            ),
        )
        self.assertIn("32 for `codex`", mutated_doc)
        self.assertIn("34 skills installed for `claude-code`", mutated_doc)

    # ------------------------------------------------------------------
    # Test 7: two `npx skills add` commands inside the SAME
    # `for agent in $AGENTS; do ... done` loop are both recognised as
    # `uses_agent_loop=True`, and all (agent, skill) pairs are covered.
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
        with _CopyFixture(
            mutated_doc=mutated_doc, mutated_yaml=mutated_yaml
        ) as fx:
            result = fx.run_validator()
        self.assertEqual(
            result.returncode,
            0,
            msg=(
                "two add commands inside one for loop must pass "
                "(regression: previously the second command's "
                f"uses_agent_loop was False); got exit={result.returncode}\n"
                f"STDOUT:\n{result.stdout}\nSTDERR: {result.stderr}"
            ),
        )

    # ------------------------------------------------------------------
    # Test 8: multiple --force occurrences across different add blocks
    # are all detected.
    # ------------------------------------------------------------------
    def test_multiple_force_flags_are_all_rejected(self) -> None:
        # Inject --force into the ksimback block AND into the caveman block.
        mutated = self._original_doc
        # ksimback block (section 6)
        mutated = mutated.replace(
            "  --agent claude-code --skill tech-debt-audit --yes",
            "  --agent claude-code --skill tech-debt-audit --force --yes",
            1,
        )
        # caveman block (section 8) — the --yes is on the same line as --skill
        mutated = mutated.replace(
            "    --agent \"$agent\" --skill caveman --yes; \\",
            "    --agent \"$agent\" --skill caveman --force --yes; \\",
            1,
        )
        self.assertNotEqual(mutated, self._original_doc)
        with _CopyFixture(mutated_doc=mutated) as fx:
            result = fx.run_validator()
        self.assertEqual(
            result.returncode,
            1,
            msg=f"multiple --force must all be rejected; got {result.returncode}\n{result.stdout}",
        )
        # Both occurrences should be mentioned.
        self.assertIn("--force", result.stdout)

    # ------------------------------------------------------------------
    # Test 9: a second add command without --yes is rejected.
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
            # Second command: missing --yes at the end.
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-review"
        )
        mutated_doc = self._replace_block(self._original_doc, new_body)
        with _CopyFixture(
            mutated_doc=mutated_doc, mutated_yaml=mutated_yaml
        ) as fx:
            result = fx.run_validator()
        self.assertEqual(
            result.returncode,
            1,
            msg=(
                "second add command missing --yes must be rejected; "
                f"got exit={result.returncode}\n{result.stdout}"
            ),
        )
        self.assertIn("--yes", result.stdout)


if __name__ == "__main__":
    unittest.main()
