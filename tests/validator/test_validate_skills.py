from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

import yaml


ROOT = Path(__file__).parents[2]
FIXTURES = Path(__file__).parent / "fixtures"
VALIDATOR_PATH = ROOT / "scripts" / "validate-skills.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_skills", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def add_skill(
        self,
        fixture: str,
        path: str | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
        requires_skills: list[str] | None = None,
        visibility: str = "public",
        clients: list[str] | None = None,
        invocation: str = "automatic",
        dependency_notes: dict[str, str] | None = None,
    ) -> dict[str, object]:
        skill_path = path or fixture
        destination = self.root / skill_path
        destination.mkdir(parents=True)
        shutil.copy(FIXTURES / fixture / "SKILL.md", destination / "SKILL.md")
        return {
            "name": name or skill_path,
            "path": skill_path,
            "description": description or "Use when exercising a validator fixture.",
            "invocation": invocation,
            "visibility": visibility,
            "clients": clients or ["agent-skills"],
            "requires_skills": requires_skills or [],
            "optional_skills": [],
            "referenced_skills": [],
            "requires_tools": [],
            "requires_commands": [],
            "aliases": [],
            "dependency_notes": dependency_notes or {},
        }

    def validate(self, entries: list[dict[str, object]]):
        manifest = {"schema_version": 1, "skills": entries}
        (self.root / "skills-manifest.yaml").write_text(
            yaml.safe_dump(manifest, sort_keys=False),
            encoding="utf-8",
        )
        return self.validator.validate_catalogue(self.root)

    def codes(self, entries: list[dict[str, object]]) -> set[str]:
        return {diagnostic.code for diagnostic in self.validate(entries)}

    def test_valid_skill_has_no_errors(self) -> None:
        entries = [self.add_skill("valid-skill")]
        diagnostics = self.validate(entries)
        self.assertFalse([item for item in diagnostics if item.severity == "error"])

    def test_missing_skill_file_has_stable_identifier(self) -> None:
        entry = self.add_skill("valid-skill")
        (self.root / "valid-skill" / "SKILL.md").unlink()
        self.assertIn("E001_SKILL_FILE_MISSING", self.codes([entry]))

    def test_missing_frontmatter_has_stable_identifier(self) -> None:
        entry = self.add_skill("invalid-frontmatter")
        self.assertIn("E002_FRONTMATTER_MISSING", self.codes([entry]))

    def test_malformed_yaml_has_stable_identifier(self) -> None:
        entry = self.add_skill("malformed-yaml")
        self.assertIn("E003_FRONTMATTER_YAML", self.codes([entry]))

    def test_folder_name_mismatch_has_stable_identifier(self) -> None:
        entry = self.add_skill("mismatched-name", name="different-name")
        self.assertIn("E006_NAME_MISMATCH", self.codes([entry]))

    def test_broken_link_has_stable_identifier(self) -> None:
        entry = self.add_skill("missing-reference")
        self.assertIn("E013_BROKEN_LINK", self.codes([entry]))

    def test_links_inside_fenced_examples_are_not_resolved(self) -> None:
        entry = self.add_skill("valid-skill")
        skill = self.root / "valid-skill" / "SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8")
            + "\n```md\n[Example only](missing/example.md)\n```\n",
            encoding="utf-8",
        )
        self.assertNotIn("E013_BROKEN_LINK", self.codes([entry]))

    def test_missing_dependency_has_stable_identifier(self) -> None:
        entry = self.add_skill("valid-skill", requires_skills=["absent-skill"])
        self.assertIn("E015_SKILL_DEPENDENCY_MISSING", self.codes([entry]))

    def test_automatic_skill_must_explain_required_manual_dependency(self) -> None:
        automatic = self.add_skill(
            "valid-skill",
            requires_skills=["manual-dependency"],
        )
        manual = self.add_skill(
            "valid-skill",
            path="manual-dependency",
            name="manual-dependency",
            invocation="manual",
        )
        skill = self.root / "manual-dependency" / "SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8").replace(
                "name: valid-skill",
                "name: manual-dependency\ndisable-model-invocation: true",
            ),
            encoding="utf-8",
        )
        self.assertIn("E028_MANUAL_DEPENDENCY", self.codes([automatic, manual]))

    def test_documented_manual_dependency_is_allowed(self) -> None:
        automatic = self.add_skill(
            "valid-skill",
            requires_skills=["manual-dependency"],
            dependency_notes={
                "manual-dependency": "The user explicitly selects this hand-off workflow."
            },
        )
        manual = self.add_skill(
            "valid-skill",
            path="manual-dependency",
            name="manual-dependency",
            invocation="manual",
        )
        skill = self.root / "manual-dependency" / "SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8").replace(
                "name: valid-skill",
                "name: manual-dependency\ndisable-model-invocation: true",
            ),
            encoding="utf-8",
        )
        self.assertNotIn("E028_MANUAL_DEPENDENCY", self.codes([automatic, manual]))

    def test_required_dependency_must_support_a_compatible_client(self) -> None:
        portable = self.add_skill(
            "valid-skill",
            requires_skills=["client-specific"],
        )
        client_specific = self.add_skill(
            "valid-skill",
            path="client-specific",
            name="client-specific",
            clients=["codex"],
        )
        skill = self.root / "client-specific" / "SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8")
            .replace("name: valid-skill", "name: client-specific")
            .replace(
                "description:",
                "compatibility: Requires Codex.\ndescription:",
            ),
            encoding="utf-8",
        )
        self.assertIn("E029_INCOMPATIBLE_DEPENDENCY", self.codes([portable, client_specific]))

    def test_excessively_long_description_has_stable_identifier(self) -> None:
        entry = self.add_skill("valid-skill")
        skill = self.root / "valid-skill" / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        text = text.replace(
            "Use when validating a minimal well-formed skill fixture.",
            "Use when " + ("a" * 501),
        )
        skill.write_text(text, encoding="utf-8")
        self.assertIn("E011_DESCRIPTION_LENGTH", self.codes([entry]))

    def test_duplicate_skill_name_has_stable_identifier(self) -> None:
        first = self.add_skill("valid-skill", path="first", name="valid-skill")
        second = self.add_skill("valid-skill", path="second", name="valid-skill")
        self.assertIn("E012_DUPLICATE_NAME", self.codes([first, second]))

    def test_private_hostname_has_stable_identifier(self) -> None:
        entry = self.add_skill("private-hostname")
        self.assertIn("E018_PRIVATE_LITERAL", self.codes([entry]))

    def test_automatic_description_must_start_with_use_when(self) -> None:
        entry = self.add_skill("unsafe-description")
        self.assertIn("E010_DESCRIPTION_TRIGGER", self.codes([entry]))

    def test_disable_model_invocation_must_be_boolean(self) -> None:
        entry = self.add_skill("valid-skill")
        skill = self.root / "valid-skill" / "SKILL.md"
        text = skill.read_text(encoding="utf-8").replace(
            "description:",
            "disable-model-invocation: yes-please\ndescription:",
        )
        skill.write_text(text, encoding="utf-8")
        self.assertIn("E008_DISABLE_INVOCATION_TYPE", self.codes([entry]))

    def test_nonportable_skill_requires_compatibility_metadata(self) -> None:
        entry = self.add_skill("valid-skill", clients=["codex"])
        self.assertIn("E026_COMPATIBILITY_REQUIRED", self.codes([entry]))

    def test_skill_symlink_cannot_escape_repository(self) -> None:
        entry = self.add_skill("valid-skill")
        skill = self.root / "valid-skill" / "SKILL.md"
        external = self.root.parent / "external-skill.md"
        external.write_text(skill.read_text(encoding="utf-8"), encoding="utf-8")
        skill.unlink()
        skill.symlink_to(external)
        try:
            self.assertIn("E027_SYMLINK_OUTSIDE", self.codes([entry]))
        finally:
            external.unlink()


if __name__ == "__main__":
    unittest.main()
