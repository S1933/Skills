#!/usr/bin/env python3
"""Validate declarative trigger and behavior evaluation coverage."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import NamedTuple

import yaml


CORE_BEHAVIOR_SKILLS = {
    "brainstorming", "codex", "dispatching-parallel-agents", "git-guardrails-claude-code",
    "improve", "receiving-code-review", "repository-reconnaissance",
    "requesting-code-review", "subagent-driven-development", "systematic-debugging",
    "test-driven-development", "verification-before-completion", "writing-plans", "writing-skills",
}


class Diagnostic(NamedTuple):
    code: str
    path: str
    message: str


def load_cases(path: Path, diagnostics: list[Diagnostic]) -> list[dict[str, object]]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        diagnostics.append(Diagnostic("E100_EVAL_YAML", path.as_posix(), str(error).splitlines()[0]))
        return []
    if not isinstance(data, dict) or not isinstance(data.get("cases"), list):
        diagnostics.append(Diagnostic("E100_EVAL_YAML", path.as_posix(), "cases must be a list"))
        return []
    return [case for case in data["cases"] if isinstance(case, dict)]


def validate_evals(root: Path | str) -> list[Diagnostic]:
    root = Path(root)
    diagnostics: list[Diagnostic] = []
    manifest = yaml.safe_load((root / "skills-manifest.yaml").read_text(encoding="utf-8"))
    automatic = sorted(
        (entry for entry in manifest.get("skills", [])
        if isinstance(entry, dict) and entry.get("invocation") == "automatic"
        ), key=lambda entry: entry["name"]
    )
    for entry in automatic:
        name = entry["name"]
        trigger_path = root / "evals" / name / "trigger.yaml"
        if not trigger_path.exists():
            diagnostics.append(Diagnostic("E101_TRIGGER_SUITE_MISSING", trigger_path.as_posix(), "automatic skill needs trigger cases"))
            continue
        trigger_document = yaml.safe_load(trigger_path.read_text(encoding="utf-8"))
        if not isinstance(trigger_document, dict) or trigger_document.get("description") != entry.get("description"):
            diagnostics.append(Diagnostic("E108_TRIGGER_DESCRIPTION_STALE", trigger_path.as_posix(), "suite description must match the manifest"))
        cases = load_cases(trigger_path, diagnostics)
        positives = negatives = 0
        tags: set[str] = set()
        names: set[str] = set()
        for case in cases:
            case_name = case.get("name")
            prompt = case.get("prompt")
            expected = case.get("expected")
            if not isinstance(case_name, str) or not isinstance(prompt, str) or not isinstance(expected, dict) or not isinstance(expected.get("should_trigger"), bool):
                diagnostics.append(Diagnostic("E102_TRIGGER_CASE_INVALID", trigger_path.as_posix(), "each case needs name, prompt, and boolean expected.should_trigger"))
                continue
            if case_name in names:
                diagnostics.append(Diagnostic("E102_TRIGGER_CASE_INVALID", trigger_path.as_posix(), f"duplicate case name: {case_name}"))
            names.add(case_name)
            positives += expected["should_trigger"] is True
            negatives += expected["should_trigger"] is False
            tags.update(tag for tag in case.get("tags", []) if isinstance(tag, str))
        if positives < 5 or negatives < 5:
            diagnostics.append(Diagnostic("E103_TRIGGER_COVERAGE", trigger_path.as_posix(), f"needs at least 5 positive and 5 negative cases; found {positives}/{negatives}"))
        for required_tag in ("ambiguous", "collision"):
            if required_tag not in tags:
                diagnostics.append(Diagnostic("E104_TRIGGER_CATEGORY", trigger_path.as_posix(), f"missing {required_tag!r} tagged case"))

        if name in CORE_BEHAVIOR_SKILLS:
            behavior_path = root / "evals" / name / "behaviour.yaml"
            if not behavior_path.exists():
                diagnostics.append(Diagnostic("E105_BEHAVIOR_SUITE_MISSING", behavior_path.as_posix(), "core skill needs behavior cases"))
                continue
            behavior_cases = load_cases(behavior_path, diagnostics)
            if len(behavior_cases) < 2:
                diagnostics.append(Diagnostic("E106_BEHAVIOR_COVERAGE", behavior_path.as_posix(), "needs at least 2 behavior cases"))
            for case in behavior_cases:
                expected = case.get("expected")
                if not isinstance(case.get("name"), str) or not isinstance(case.get("prompt"), str) or not isinstance(expected, dict) or not any(isinstance(expected.get(key), list) and expected[key] for key in ("must_include", "must_not_include")):
                    diagnostics.append(Diagnostic("E107_BEHAVIOR_CASE_INVALID", behavior_path.as_posix(), "behavior case needs name, prompt, and non-empty expectation list"))
    return diagnostics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    diagnostics = validate_evals(args.root)
    for item in diagnostics:
        print(f"{item.path}: error: [{item.code}] {item.message}", file=sys.stderr)
    print(f"validated evaluations: {len(diagnostics)} error(s)")
    return 1 if diagnostics else 0


if __name__ == "__main__":
    raise SystemExit(main())
