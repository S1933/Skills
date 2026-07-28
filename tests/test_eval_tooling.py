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
        cls.bootstrap = load_script("bootstrap-evals.py")

    def test_validator_requires_trigger_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skills-manifest.yaml").write_text(
                yaml.safe_dump({"skills": [{"name": "sample", "invocation": "automatic"}]}),
                encoding="utf-8",
            )
            codes = {item.code for item in self.validator.validate_evals(root)}
            self.assertIn("E101_TRIGGER_SUITE_MISSING", codes)

    def test_validator_reports_invalid_manifest_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skills-manifest.yaml").write_text(
                yaml.safe_dump({"skills": [{"name": 42, "invocation": "automatic"}]}),
                encoding="utf-8",
            )
            codes = {item.code for item in self.validator.validate_evals(root)}
            self.assertIn("E109_EVAL_MANIFEST", codes)

    def test_validator_reports_malformed_trigger_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skills-manifest.yaml").write_text(
                yaml.safe_dump({"skills": [{"name": "sample", "invocation": "automatic", "description": "sample"}]}),
                encoding="utf-8",
            )
            trigger = root / "evals" / "sample" / "trigger.yaml"
            trigger.parent.mkdir(parents=True)
            trigger.write_text("cases: [unterminated\n", encoding="utf-8")
            codes = {item.code for item in self.validator.validate_evals(root)}
            self.assertIn("E100_EVAL_YAML", codes)

    def test_validator_reports_suite_skill_mismatch_and_orphan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skills-manifest.yaml").write_text(
                yaml.safe_dump({"skills": []}), encoding="utf-8"
            )
            suite = root / "evals" / "orphan" / "trigger.yaml"
            suite.parent.mkdir(parents=True)
            suite.write_text(
                yaml.safe_dump({"skill": "different", "description": "x", "cases": [{"name": "duplicate", "prompt": "same"}]}),
                encoding="utf-8",
            )
            (suite.parent / "behaviour.yaml").write_text(
                yaml.safe_dump({"cases": [{"name": "duplicate", "prompt": "same"}]}),
                encoding="utf-8",
            )
            codes = {item.code for item in self.validator.validate_evals(root)}
            self.assertIn("E110_EVAL_SKILL_MISMATCH", codes)
            self.assertIn("E111_EVAL_SUITE_ORPHAN", codes)
            self.assertIn("E112_EVAL_CASE_DUPLICATE", codes)

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

    def test_bootstrap_preserves_existing_trigger_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skills-manifest.yaml").write_text(
                yaml.safe_dump({"skills": [{"name": "brainstorming", "invocation": "automatic", "description": "custom"}]}),
                encoding="utf-8",
            )
            trigger = root / "evals" / "brainstorming" / "trigger.yaml"
            trigger.parent.mkdir(parents=True)
            trigger.write_text("edited: true\n", encoding="utf-8")

            self.assertEqual(0, self.bootstrap.main(["--root", str(root), "--all-missing"]))
            self.assertEqual("edited: true\n", trigger.read_text(encoding="utf-8"))

    def test_bootstrap_force_replaces_selected_trigger(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skills-manifest.yaml").write_text(
                yaml.safe_dump({"skills": [{"name": "brainstorming", "invocation": "automatic", "description": "custom"}]}),
                encoding="utf-8",
            )
            trigger = root / "evals" / "brainstorming" / "trigger.yaml"
            trigger.parent.mkdir(parents=True)
            trigger.write_text("edited: true\n", encoding="utf-8")

            self.assertEqual(0, self.bootstrap.main(["--root", str(root), "--skill", "brainstorming", "--force"]))
            self.assertNotEqual("edited: true\n", trigger.read_text(encoding="utf-8"))

    def test_bootstrap_rejects_unknown_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skills-manifest.yaml").write_text(
                yaml.safe_dump({"skills": []}), encoding="utf-8"
            )
            self.assertEqual(2, self.bootstrap.main(["--root", str(root), "--skill", "missing"]))


if __name__ == "__main__":
    unittest.main()
