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
        word_budget: int | None = None,
    ) -> dict[str, object]:
        skill_path = path or fixture
        destination = self.root / skill_path
        destination.mkdir(parents=True)
        shutil.copy(FIXTURES / fixture / "SKILL.md", destination / "SKILL.md")
        entry = {
            "name": name or skill_path,
            "path": skill_path,
            "description": description or "Use when validating a minimal well-formed skill fixture.",
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
            "approximate_word_count": len(
                (destination / "SKILL.md").read_text(encoding="utf-8").split()
            ),
        }
        if word_budget is not None:
            entry["word_budget"] = word_budget
        return entry

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

    def test_manifest_rejects_unsafe_path_and_unknown_enums(self) -> None:
        entry = self.add_skill("valid-skill")
        entry["path"] = "../outside"
        entry["visibility"] = "secret"
        entry["invocation"] = "sometimes"
        entry["clients"] = ["unknown-client"]
        self.assertIn("E042_MANIFEST_SCHEMA", self.codes([entry]))

    def test_manifest_rejects_wrong_collection_types(self) -> None:
        entry = self.add_skill("valid-skill")
        entry["clients"] = "agent-skills"
        entry["supporting_files"] = "valid-skill/SKILL.md"
        self.assertIn("E042_MANIFEST_SCHEMA", self.codes([entry]))

    def test_manifest_entry_must_be_a_mapping(self) -> None:
        (self.root / "skills-manifest.yaml").write_text(
            yaml.safe_dump({"skills": ["invalid"]}), encoding="utf-8"
        )
        codes = {item.code for item in self.validator.validate_catalogue(self.root)}
        self.assertIn("E042_MANIFEST_SCHEMA", codes)

    def test_supporting_file_must_belong_to_skill_or_shared_area(self) -> None:
        entry = self.add_skill("valid-skill")
        unrelated = self.root / "unrelated.txt"
        unrelated.write_text("unrelated", encoding="utf-8")
        entry["supporting_files"] = ["unrelated.txt"]
        self.assertIn("E043_PATH_OUTSIDE_SKILL", self.codes([entry]))

    def test_any_symlink_under_skill_cannot_escape_repository(self) -> None:
        entry = self.add_skill("valid-skill")
        with tempfile.TemporaryDirectory() as external:
            target = Path(external) / "outside.txt"
            target.write_text("outside", encoding="utf-8")
            (self.root / "valid-skill" / "outside-link.txt").symlink_to(target)
            self.assertIn("E027_SYMLINK_OUTSIDE", self.codes([entry]))

    def test_absolute_supporting_symlink_is_rejected_without_crashing(self) -> None:
        entry = self.add_skill("valid-skill")
        with tempfile.TemporaryDirectory() as external:
            target = Path(external) / "outside.txt"
            target.write_text("outside", encoding="utf-8")
            link = Path(external) / "link.txt"
            link.symlink_to(target)
            entry["supporting_files"] = [str(link)]
            self.assertIn("E042_MANIFEST_SCHEMA", self.codes([entry]))

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

    def test_deliberately_invalid_flowchart_example_is_not_compiled_as_dot(self) -> None:
        source = self.root / "guide.md"
        source.write_text(
            "# Flowchart reference\n\n"
            "The anti-pattern lanes are intentionally not DOT fences so graphviz "
            "compilation is skipped:\n\n"
            "```md\nstep1 [label=\"start\"]\nstep1 -> step2\n```\n",
            encoding="utf-8",
        )
        diagnostics = []
        blocks = self.validator.validate_examples(source, self.root, diagnostics)
        self.assertFalse(
            any(block.lstrip().startswith("step1 [") for block in blocks),
            "the anti-pattern fragment must use a non-DOT fence",
        )

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

    def test_manifest_description_must_match_frontmatter(self) -> None:
        entry = self.add_skill(
            "valid-skill",
            description="Use when this stale manifest description no longer matches.",
        )
        self.assertIn("E036_MANIFEST_DESCRIPTION_MISMATCH", self.codes([entry]))

    def test_manifest_word_count_cannot_be_stale(self) -> None:
        entry = self.add_skill("valid-skill")
        entry["approximate_word_count"] = 9999
        self.assertIn("E037_MANIFEST_WORD_COUNT_STALE", self.codes([entry]))

    def test_declared_main_file_word_budget_is_enforced(self) -> None:
        entry = self.add_skill("valid-skill", word_budget=10)
        self.assertIn("E035_WORD_BUDGET", self.codes([entry]))

    def test_default_main_file_word_budget_is_enforced(self) -> None:
        entry = self.add_skill("valid-skill")
        skill = self.root / "valid-skill" / "SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8") + "\n" + ("word " * 801),
            encoding="utf-8",
        )
        self.assertIn("E035_WORD_BUDGET", self.codes([entry]))

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
