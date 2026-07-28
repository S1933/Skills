from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


class SharedContractTests(unittest.TestCase):
    def test_contract_files_exist(self) -> None:
        expected = (
            ROOT / "repository-reconnaissance" / "SKILL.md",
            ROOT / "references" / "evidence-standard.md",
            ROOT / "references" / "execution-safety.md",
        )
        for path in expected:
            with self.subTest(path=path):
                self.assertTrue(path.is_file())

    def test_audit_skills_route_to_every_shared_contract(self) -> None:
        required_markers = (
            "repository-reconnaissance",
            "../references/evidence-standard.md",
            "../references/execution-safety.md",
        )
        for skill_name in (
            "improve",
            "tech-debt-audit",
            "improve-codebase-architecture",
        ):
            text = (ROOT / skill_name / "SKILL.md").read_text(encoding="utf-8")
            for marker in required_markers:
                with self.subTest(skill=skill_name, marker=marker):
                    self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
