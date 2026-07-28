from pathlib import Path
import importlib.util
import tempfile
import unittest

import yaml


ROOT = Path(__file__).parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EvalToolingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_script("validate-evals.py")
        cls.scorer = load_script("score-evals.py")

    def test_validator_requires_trigger_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skills-manifest.yaml").write_text(
                yaml.safe_dump({"skills": [{"name": "sample", "invocation": "automatic"}]}),
                encoding="utf-8",
            )
            codes = {item.code for item in self.validator.validate_evals(root)}
            self.assertIn("E101_TRIGGER_SUITE_MISSING", codes)

    def test_scorer_calculates_core_metrics(self) -> None:
        observations = {
            "observations": [
                {"expected_trigger": True, "triggered": True, "compliant": True, "collision": False, "context_tokens": 100},
                {"expected_trigger": False, "triggered": False, "compliant": None, "collision": False, "context_tokens": 0},
                {"expected_trigger": False, "triggered": True, "compliant": False, "collision": True, "context_tokens": 100},
            ]
        }
        metrics = self.scorer.score(observations)
        self.assertEqual(0.5, metrics["trigger_precision"])
        self.assertEqual(1.0, metrics["trigger_recall"])
        self.assertEqual(0.5, metrics["compliance_rate"])
        self.assertEqual(1 / 3, metrics["collision_rate"])


if __name__ == "__main__":
    unittest.main()
