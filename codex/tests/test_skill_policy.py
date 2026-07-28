"""Regression tests for the Codex skill's execution-safety contract."""

from pathlib import Path
import re
import unittest


SKILL_PATH = Path(__file__).parents[1] / "SKILL.md"


class CodexSkillSafetyPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL_PATH.read_text(encoding="utf-8")

    def test_research_defaults_to_an_explicit_read_only_sandbox(self) -> None:
        self.assertIn(
            'codex exec --sandbox read-only --ephemeral "<prompt>"',
            self.skill,
        )

    def test_bypass_is_not_presented_before_elevated_execution_policy(self) -> None:
        ordinary_guidance, separator, _ = self.skill.partition("## Elevated execution")
        self.assertTrue(separator, "missing Elevated execution policy")
        unrestricted_options = (
            "--dangerously-bypass-approvals-and-sandbox",
            "--sandbox danger-full-access",
        )
        for option in unrestricted_options:
            with self.subTest(option=option):
                self.assertNotIn(option, ordinary_guidance)

    def test_all_unrestricted_modes_are_covered_by_elevated_policy(self) -> None:
        _, separator, elevated_guidance = self.skill.partition("## Elevated execution")
        self.assertTrue(separator, "missing Elevated execution policy")
        self.assertIn("--sandbox danger-full-access", elevated_guidance)
        self.assertIn(
            "--dangerously-bypass-approvals-and-sandbox",
            elevated_guidance,
        )

    def test_elevated_execution_requires_immediate_explicit_confirmation(self) -> None:
        _, separator, elevated_guidance = self.skill.partition("## Elevated execution")
        self.assertTrue(separator, "missing Elevated execution policy")
        required_phrases = (
            "explicitly asks for unrestricted execution",
            "exact command and risks",
            "confirms immediately before execution",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, elevated_guidance)

    def test_write_access_requires_an_explicit_user_request(self) -> None:
        self.assertRegex(
            self.skill,
            re.compile(
                r"write access.*explicit user request",
                re.IGNORECASE | re.DOTALL,
            ),
        )

    def test_model_catalogue_is_not_hard_coded(self) -> None:
        self.assertIsNone(
            re.search(r"\bgpt-\d", self.skill, re.IGNORECASE),
            "model names must come from current Codex CLI help/configuration",
        )


if __name__ == "__main__":
    unittest.main()
