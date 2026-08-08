from pathlib import Path
import importlib.util
import tempfile
import unittest

import yaml


ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "scripts" / "generate-catalogue.py"


class CatalogueGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("generate_catalogue", SCRIPT)
        if spec is None or spec.loader is None:
            raise RuntimeError(SCRIPT)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_checked_in_catalogue_is_current(self) -> None:
        manifest = yaml.safe_load((ROOT / "skills-manifest.yaml").read_text(encoding="utf-8"))
        self.assertEqual(self.module.render_readme(manifest), (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(self.module.render_catalogue(manifest), (ROOT / "docs/generated/catalogue.md").read_text(encoding="utf-8"))

    def test_table_cells_escape_markdown_and_output_is_deterministic(self) -> None:
        manifest = {"skills": [{
            "name": "sample", "path": "sample", "visibility": "public",
            "invocation": "manual", "clients": ["codex"],
            "description": "first | second\nline", "approximate_word_count": 1,
        }]}
        first = self.module.render_readme(manifest)
        self.assertEqual(first, self.module.render_readme(manifest))
        self.assertIn(r"first \| second<br>line", first)

    def test_invalid_manifest_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skills-manifest.yaml").write_text("skills: invalid\n", encoding="utf-8")
            self.assertEqual(2, self.module.main(["--root", str(root), "--check"]))

    def test_render_failure_does_not_partially_replace_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skills-manifest.yaml").write_text(
                yaml.safe_dump({"skills": [{
                    "name": "sample", "path": "sample", "visibility": "public",
                    "invocation": "manual", "description": "sample", "clients": [],
                }]}),
                encoding="utf-8",
            )
            readme = root / "README.md"
            readme.write_text("preserve me\n", encoding="utf-8")
            self.assertEqual(2, self.module.main(["--root", str(root)]))
            self.assertEqual("preserve me\n", readme.read_text(encoding="utf-8"))
            self.assertFalse((root / "docs" / "generated" / "catalogue.md").exists())


if __name__ == "__main__":
    unittest.main()
