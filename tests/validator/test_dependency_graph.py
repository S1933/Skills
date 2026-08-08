from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

import yaml


ROOT = Path(__file__).parents[2]
GENERATOR_PATH = ROOT / "scripts" / "generate-dependency-graph.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_dependency_graph", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load dependency graph generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DependencyGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()

    def test_checked_in_graph_matches_manifest(self) -> None:
        manifest = yaml.safe_load(
            (ROOT / "skills-manifest.yaml").read_text(encoding="utf-8")
        )
        expected = self.generator.render_dependency_graph(manifest)
        actual = (ROOT / "docs" / "generated" / "dependency-graph.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(expected, actual)

    def test_renderer_sorts_skills_and_distinguishes_edge_types(self) -> None:
        manifest = {
            "skills": [
                {
                    "name": "zeta",
                    "requires_skills": ["beta"],
                    "optional_skills": ["alpha"],
                },
                {"name": "alpha", "requires_skills": [], "optional_skills": []},
                {"name": "beta", "requires_skills": [], "optional_skills": []},
            ]
        }
        output = self.generator.render_dependency_graph(manifest)
        self.assertIn('zeta -->|requires| beta', output)
        self.assertIn('zeta -. optional .-> alpha', output)
        self.assertLess(output.index("| alpha |"), output.index("| zeta |"))

    def test_invalid_manifest_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skills-manifest.yaml").write_text("skills: invalid\n", encoding="utf-8")
            self.assertEqual(2, self.generator.main(["--root", str(root), "--check"]))

    def test_invalid_dependency_collection_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skills-manifest.yaml").write_text(
                yaml.safe_dump({"skills": [{"name": "sample", "requires_skills": 3}]}),
                encoding="utf-8",
            )
            self.assertEqual(2, self.generator.main(["--root", str(root), "--check"]))


if __name__ == "__main__":
    unittest.main()
