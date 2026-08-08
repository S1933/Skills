"""Mutation tests for scripts/validate-external-skills.py.

These tests intentionally corrupt a COPY of `docs/migration-npx.md` (and
sometimes `external-skills.yaml`) in a `TemporaryDirectory` to verify
that the validator rejects four classes of broken migration
configuration that a prior review of the validator found it accepted by
accident:

1. Removing `--global` from an `npx skills add` command.
2. Removing `--copy` from an `npx skills add` command.
3. A source declared for several agents (e.g. claude-code AND codex),
   but the install block only uses `--agent claude-code` (missing agent
   coverage).
4. A single fenced ```` ```bash ```` block containing two `npx skills
   add` commands where the second targets an undeclared source — the
   prior parser only saw the first command and silently passed.

The tests run the validator as a subprocess against the mutated copy
via the new CLI args / env-var path API, asserting on the exit code.
This is the most faithful way to exercise the validator (it covers the
script's `main()` and CLI exit code, not just the helpers).

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
        self._original_validator = _load_validator()

    # --- Sanity check: the baseline (real files) must still validate. ---
    def test_baseline_passes(self) -> None:
        # Run against the real files via the default (no-arg) path so we
        # also exercise the original default-paths code path.
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

    # --- Mode 3: declared agent missing from a non-loop install must fail. ---
    def test_declared_agent_without_install_coverage_is_rejected(self) -> None:
        import yaml

        data = yaml.safe_load(self._original_yaml)
        for src in data.get("sources", []):
            if src.get("name") == "ksimback/tech-debt-skill":
                src["agents"] = ["claude-code", "codex"]
                src["claude_code_only"] = False
        mutated_yaml = yaml.safe_dump(data, sort_keys=False)

        # The single existing install block for ksimback only covers
        # --agent claude-code. No loop, no second add command for
        # codex, so codex has no install coverage. The validator must
        # reject.
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
        # Should mention the missing agent (codex) and/or the union
        # coverage check.
        self.assertTrue(
            "codex" in result.stdout
            and (
                "missing coverage" in result.stdout
                or "no install block installs on them" in result.stdout
                or "no install command in" in result.stdout
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

    def test_two_commands_with_distinct_agents_and_skills_no_cross_contamination(
        self,
    ) -> None:
        """Per-command parser must NOT bleed flags/agents/skills between commands.

        With the previous (buggy) splitter, both commands inherited the
        full --agent and --skill sets. Verify that the per-command
        AddBlocks carry ONLY their own command's metadata.
        """
        body = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes\n"
            "npx --yes skills@latest add ayghri/i-have-adhd --global --copy \\\n"
            "  --agent codex --skill i-have-adhd --yes"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        self.assertEqual(len(blocks), 2, f"expected 2 AddBlocks, got {len(blocks)}")
        # First command: only claude-code + tech-debt-audit.
        self.assertEqual(blocks[0].source, "ksimback/tech-debt-skill")
        self.assertEqual(blocks[0].literal_agents, ["claude-code"])
        self.assertEqual(blocks[0].skills, ["tech-debt-audit"])
        # Second command: only codex + i-have-adhd — must NOT inherit
        # the first command's --agent or --skill.
        self.assertEqual(blocks[1].source, "ayghri/i-have-adhd")
        self.assertEqual(blocks[1].literal_agents, ["codex"])
        self.assertEqual(blocks[1].skills, ["i-have-adhd"])
        # Flag checks are per-command: both must still report --global
        # and --copy even though the segments are on separate lines.
        for b in blocks:
            self.assertTrue(b.has_global_flag)
            self.assertTrue(b.has_copy_flag)
            self.assertFalse(b.uses_agent_loop)

    def test_for_loop_preamble_is_folded_into_command(self) -> None:
        """A `for agent in $AGENTS; do \\` opener must mark the FOLLOWING
        add command as `uses_agent_loop=True`, not be dropped.

        This guards against a regression where the splitter mistakenly
        treated the `for ... do` line as a separate (and therefore
        dropped) segment.
        """
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
        # `$agent` is not a literal agent; the loop's reach is checked
        # against $AGENTS instead.
        self.assertEqual(blocks[0].literal_agents, [])

    def test_two_commands_in_same_loop_both_get_uses_agent_loop(self) -> None:
        """REGRESSION: a for loop with TWO `npx skills add` commands.

        The prior splitter attached the `for ... do` preamble only to
        the FIRST add command, so the second command in the loop got
        `uses_agent_loop=False` and no literal agents — and the
        validator rejected a perfectly valid shell configuration. This
        test exercises the fix: once a `for ... do` has been seen, the
        `in_agent_loop` state persists across every subsequent add
        command in the block until a `done` closes the loop.
        """
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
        self.assertTrue(
            blocks[0].uses_agent_loop,
            "first command inside the for loop must report uses_agent_loop=True",
        )
        self.assertEqual(blocks[1].source, "source1/foo")
        self.assertEqual(blocks[1].skills, ["b"])
        self.assertTrue(
            blocks[1].uses_agent_loop,
            "second command inside the same for loop must also report "
            "uses_agent_loop=True (regression: was False before the fix)",
        )
        # And neither command should have a literal agent, since both
        # rely on the loop's $agent expansion.
        self.assertEqual(blocks[0].literal_agents, [])
        self.assertEqual(blocks[1].literal_agents, [])

    def test_done_resets_loop_state(self) -> None:
        """A `done` closes the loop; commands after it are NOT in the loop.

        Without the reset, a follow-up literal add command (no `for`)
        would incorrectly inherit `uses_agent_loop=True`.
        """
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
        self.assertTrue(
            blocks[0].uses_agent_loop,
            "command inside the loop must report uses_agent_loop=True",
        )
        self.assertEqual(blocks[1].source, "outside/bar")
        self.assertFalse(
            blocks[1].uses_agent_loop,
            "command AFTER `done` must not inherit the loop marker",
        )
        self.assertEqual(blocks[1].literal_agents, ["claude-code"])

    def test_split_at_semicolon_within_block(self) -> None:
        """A `;`-separated block (e.g. `remove` then `add` on the same
        line) must yield exactly one AddBlock, for the add command.

        The remove command must not pollute the add command's flags.
        """
        body = (
            "npx --yes skills@latest remove --global --agent claude-code "
            "--skill foo --yes; \\\n"
            "npx --yes skills@latest add ksimback/tech-debt-skill "
            "--global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes"
        )
        blocks = self.validator.parse_add_blocks(f"```bash\n{body}\n```\n")
        # Only the `add` produces an AddBlock; `remove` is dropped.
        self.assertEqual(len(blocks), 1, f"expected 1 AddBlock, got {len(blocks)}")
        self.assertEqual(blocks[0].source, "ksimback/tech-debt-skill")
        self.assertEqual(blocks[0].literal_agents, ["claude-code"])
        self.assertEqual(blocks[0].skills, ["tech-debt-audit"])


class ValidateExternalSkillsRegressionTests(unittest.TestCase):
    """End-to-end regression tests for the per-command + union refactor.

    Each test stages a copy of the real files in a `TemporaryDirectory`,
    mutates the copy so the validator sees a specific edge case, runs
    the validator as a subprocess against the copy via the env-var
    API, and asserts on the exit code. The real tracked files are
    never touched. These tests are the safety net against the
    cross-contamination bug and the missing union check.
    """

    def setUp(self) -> None:
        self._original_doc = MIGRATION_DOC.read_text(encoding="utf-8")
        self._original_yaml = EXTERNAL_YAML.read_text(encoding="utf-8")
        self._original_validator = _load_validator()

    # ------------------------------------------------------------------
    # Helpers for swapping out a fenced block and the YAML declaration.
    # All helpers only operate on the COPY in the active `_CopyFixture`
    # — they never write to the real repo files.
    # ------------------------------------------------------------------
    @staticmethod
    def _replace_block(doc: str, new_body: str) -> str:
        r"""Replace the fenced block whose body matches the ksimback single
        install with `new_body`. The body is wrapped in a ```bash ... ```
        fence. Returns the rewritten doc.
        """
        old_block = (
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes"
        )
        new_block = new_body.rstrip()
        new_doc = doc.replace(old_block, new_block, 1)
        assert new_doc != doc, "test setup: ksimback block not found"
        return new_doc

    def _mutate_yaml(self, base_yaml: str, mutate_fn) -> str:
        """Apply `mutate_fn(data)` to a parsed YAML copy and return the
        mutated YAML text. The original is never written back."""
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
        """Return a YAML string with the declaration for `name` updated.

        Fields left as `None` are not changed. The base YAML is read
        from the supplied string; the result is a NEW string.
        """
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
        """Return a YAML string with a maintained_locally entry set
        (replaced if it exists, else appended)."""
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
        # Declare two skills for ksimback (still only claude-code) so the
        # second add command has a different, declared skill to install.
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
        # The error should mention the missing --copy on the SECOND
        # command. The per-command parser must attribute the missing
        # flag to the correct command, not silently merge it with the
        # first command's flags.
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
    # Test 3: two commands with distinct agents and skills (no
    # cross-contamination) pass.
    #
    # The per-command parser must yield TWO AddBlocks, one per command,
    # each with ONLY its own --agent and --skill set. The validator
    # must accept this layout and return exit=0.
    # ------------------------------------------------------------------
    def test_two_commands_distinct_agents_and_skills_pass(self) -> None:
        # The source is declared for two agents and two skills, with
        # `claude_code_only=False` so the prose count is consistent.
        mutated_yaml = self._set_yaml_source(
            self._original_yaml,
            "ksimback/tech-debt-skill",
            selection=["tech-debt-audit", "tech-debt-review"],
            agents=["claude-code", "codex"],
            claude_code_only=False,
        )
        # Update the prose count: declared_total goes 33 -> 34
        # (added tech-debt-review). The ksimback source is no longer
        # claude_code_only, so the claude-only count drops 1 -> 0
        # and expected_other = 34 - 0 = 34. Claude-code total is
        # also 34.
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
            0,
            msg=(
                "two commands with distinct agents and skills must pass; "
                f"got exit={result.returncode}\n{result.stdout}\n"
                f"STDERR: {result.stderr}"
            ),
        )

    # ------------------------------------------------------------------
    # Test 4: two literal commands, each covering one agent, are
    # accepted when their union covers the declaration.
    #
    # This is the explicit union-coverage test. The source declares
    # three agents; the doc only has two commands, one for claude-code
    # and one for codex+opencode. The validator must accept this
    # because the union {claude-code, codex, opencode} equals the
    # declared agent set.
    # ------------------------------------------------------------------
    def test_two_commands_union_covers_declaration_passes(self) -> None:
        mutated_yaml = self._set_yaml_source(
            self._original_yaml,
            "ksimback/tech-debt-skill",
            selection=["tech-debt-audit", "tech-debt-review"],
            agents=["claude-code", "codex", "opencode"],
            claude_code_only=False,
        )
        # Update prose count: 33 -> 34 declared, claude_code_only 1 -> 0
        # (ksimback is no longer claude-only) so other-agents = 34.
        mutated_doc = self._original_doc
        mutated_doc = mutated_doc.replace(
            "**33 skills installed for `claude-code`; 32 for `codex`",
            "**34 skills installed for `claude-code`; 34 for `codex`",
            1,
        )
        new_body = (
            # First command: covers claude-code.
            "npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \\\n"
            "  --agent claude-code --skill tech-debt-audit --yes\n"
            # Second command: covers codex AND opencode.
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
                "union of two commands must cover the declaration; "
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
        # Prose count: declared_total=34, other-agents=34. The union
        # check (Check 3e) is what must trigger; the prose count is
        # internally consistent for the OTHER sources.
        mutated_doc = self._original_doc
        mutated_doc = mutated_doc.replace(
            "**33 skills installed for `claude-code`; 32 for `codex`",
            "**34 skills installed for `claude-code`; 34 for `codex`",
            1,
        )
        new_body = (
            # Only covers claude-code and codex; opencode has no
            # install command anywhere.
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
        # The error must mention the missing agent (`opencode`) and the
        # union-coverage message.
        self.assertIn("opencode", result.stdout)
        self.assertIn("no install command", result.stdout)

    # ------------------------------------------------------------------
    # Test 6: a local Claude-only selection is subtracted from the
    # other-agents total (Change C regression).
    #
    # The bug: Check 4 only counted `claude_code_only` skills in
    # `data["sources"]`, ignoring `data["maintained_locally"]`. A
    # local claude-only skill would inflate the "other agents" prose
    # count by 1. This test adds a local claude-only skill and asserts
    # the validator passes — meaning the prose count is computed
    # correctly across BOTH sections.
    # ------------------------------------------------------------------
    def test_local_claude_only_subtracted_from_other_agents_total(self) -> None:
        # Add a new local source with one claude-only skill. The
        # `claude_code_only=True` flag means the source DECLARES
        # only claude-code as its agent; the other-agents total is
        # reduced by 1 because the prose counts the skill only on
        # claude-code. The validator will require an install block
        # for it; provide one targeting only claude-code.
        mutated_yaml = self._set_yaml_maintained(
            self._original_yaml,
            "private-skills",
            selection=["private-claude-only-skill"],
            agents=["claude-code"],
            claude_code_only=True,
        )
        # Update prose count: declared_total goes 33 -> 34 (added one
        # local skill). Claude-code total goes 33 -> 34. Other-agents:
        # the new local skill is claude_code_only so it is subtracted
        # from the other-agents total: 32 stays 32.
        mutated_doc = self._original_doc
        mutated_doc = mutated_doc.replace(
            "**33 skills installed for `claude-code`; 32 for `codex`",
            "**34 skills installed for `claude-code`; 32 for `codex`",
            1,
        )
        # Inject a new fenced block for the new local source. The
        # install is for claude-code only (matching the
        # `claude_code_only` declaration). Place it just before the
        # "## 10. Verify" section.
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
        # Spot-check: the prose line in the live doc still says 32 for
        # the other agents, which is the corrected subtraction. The
        # baseline doc had 32; the new doc still has 32 (the new
        # claude-only skill was correctly subtracted).
        self.assertIn("32 for `codex`", mutated_doc)
        self.assertIn("34 skills installed for `claude-code`", mutated_doc)

    # ------------------------------------------------------------------
    # Test 7: REGRESSION — two `npx skills add` commands inside the
    # SAME `for agent in $AGENTS; do ... done` loop are both
    # recognized as `uses_agent_loop=True`, and the union of their
    # agent reach covers the declaration.
    #
    # The prior splitter attached the `for ... do` preamble only to
    # the FIRST add command, so the second command got
    # `uses_agent_loop=False` with no literal agents, and the
    # validator rejected a perfectly valid shell configuration. This
    # end-to-end test exercises the fix against the real main(): we
    # assemble a valid `for` loop with two `add` commands targeting
    # a declared source, run the validator, and assert exit=0.
    # ------------------------------------------------------------------
    def test_two_add_commands_inside_one_for_loop_passes(self) -> None:
        # Declare the source for the SAME agent set the for-loop will
        # iterate over. The validator's Check 3b requires that every
        # agent in $AGENTS be present in the source's declared agents
        # list, so the declaration must include them all.
        mutated_yaml = self._set_yaml_source(
            self._original_yaml,
            "ksimback/tech-debt-skill",
            selection=["tech-debt-audit", "tech-debt-review"],
            agents=["claude-code", "codex", "opencode", "cursor"],
            claude_code_only=False,
        )
        # Update the prose count to match the new declaration.
        # declared_total=34, claude_code_only=0 (ksimback no longer
        # claude-only) so other-agents=34 too. claude-code=34.
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


if __name__ == "__main__":
    unittest.main()
