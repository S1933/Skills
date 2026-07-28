from pathlib import Path
import importlib.util
import unittest

import yaml


ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "scripts" / "generate-catalogue.py"


class CatalogueGenerationTests(unittest.TestCase):
    def test_checked_in_catalogue_is_current(self) -> None:
        spec = importlib.util.spec_from_file_location("generate_catalogue", SCRIPT)
        if spec is None or spec.loader is None:
            raise RuntimeError(SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        manifest = yaml.safe_load((ROOT / "skills-manifest.yaml").read_text(encoding="utf-8"))
        self.assertEqual(module.render_readme(manifest), (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(module.render_catalogue(manifest), (ROOT / "docs/generated/catalogue.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
