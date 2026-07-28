from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "classify-git-command.py"


def load_classifier():
    spec = importlib.util.spec_from_file_location("git_guardrail_classifier", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.classifier = load_classifier()

    def test_nested_shell_wrapper_is_blocked(self) -> None:
        decision = self.classifier.classify_command(
            "bash -c \"sh -c 'git push origin main'\""
        )
        self.assertEqual("GIT_GUARDRAIL_BLOCKED", decision.code)
        self.assertEqual("push", decision.detail)

    def test_git_executable_alias_is_blocked(self) -> None:
        decision = self.classifier.classify_command(
            "git -c alias.publish='!git push origin main' publish"
        )
        self.assertEqual("GIT_GUARDRAIL_BLOCKED", decision.code)

    def test_git_alias_section_is_case_insensitive(self) -> None:
        decision = self.classifier.classify_command(
            "git -c Alias.publish='!git push origin main' publish"
        )
        self.assertEqual("GIT_GUARDRAIL_BLOCKED", decision.code)

    def test_git_alias_name_is_case_insensitive(self) -> None:
        decision = self.classifier.classify_command(
            "git -c alias.Publish='!git push origin main' publish"
        )
        self.assertEqual("GIT_GUARDRAIL_BLOCKED", decision.code)

    def test_last_git_alias_configuration_value_wins(self) -> None:
        decision = self.classifier.classify_command(
            "git -c alias.publish='!git status' "
            "-c alias.publish='!git push origin main' publish"
        )
        self.assertEqual("GIT_GUARDRAIL_BLOCKED", decision.code)

    def test_non_shell_git_alias_is_inspected(self) -> None:
        decision = self.classifier.classify_command(
            "git -c alias.publish='push origin main' publish"
        )
        self.assertEqual("GIT_GUARDRAIL_BLOCKED", decision.code)

    def test_config_env_alias_fails_closed(self) -> None:
        decision = self.classifier.classify_command(
            "ALIAS_BODY='!git push origin main' "
            "git --config-env=alias.publish=ALIAS_BODY publish"
        )
        self.assertEqual("GIT_GUARDRAIL_BLOCKED", decision.code)

    def test_wrapper_option_boundaries_cannot_hide_git(self) -> None:
        for command in (
            "bash -c -- 'git push origin main'",
            "eval -- 'git clean -fd'",
            'env -S "bash -c \'git push origin main\'"',
        ):
            with self.subTest(command=command):
                decision = self.classifier.classify_command(command)
                self.assertEqual("GIT_GUARDRAIL_BLOCKED", decision.code)

    def test_benign_shell_wrapper_is_allowed(self) -> None:
        self.assertIsNone(self.classifier.classify_command("bash -c 'git status'"))


if __name__ == "__main__":
    unittest.main()
