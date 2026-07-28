#!/usr/bin/env python3
"""Score observed evaluation outcomes produced by any client-specific runner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def score(data: dict[str, object]) -> dict[str, float | int | None]:
    rows = [row for row in data.get("observations", []) if isinstance(row, dict)]
    true_positive = sum(row.get("expected_trigger") is True and row.get("triggered") is True for row in rows)
    false_positive = sum(row.get("expected_trigger") is False and row.get("triggered") is True for row in rows)
    false_negative = sum(row.get("expected_trigger") is True and row.get("triggered") is False for row in rows)
    compliance = [row.get("compliant") for row in rows if isinstance(row.get("compliant"), bool)]
    contexts = [row["context_tokens"] for row in rows if isinstance(row.get("context_tokens"), int)]
    groups: dict[str, list[bool]] = {}
    for row in rows:
        if isinstance(row.get("run_group"), str) and isinstance(row.get("triggered"), bool):
            groups.setdefault(row["run_group"], []).append(row["triggered"])
    repeated = [values for values in groups.values() if len(values) > 1]
    stable = sum(len(set(values)) == 1 for values in repeated)
    return {
        "trigger_precision": ratio(true_positive, true_positive + false_positive),
        "trigger_recall": ratio(true_positive, true_positive + false_negative),
        "compliance_rate": ratio(sum(compliance), len(compliance)),
        "collision_rate": ratio(sum(row.get("collision") is True for row in rows), len(rows)),
        "average_context_tokens": ratio(sum(contexts), len(contexts)),
        "stability": ratio(stable, len(repeated)),
        "observations": len(rows),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    args = parser.parse_args(argv)
    data = yaml.safe_load(args.results.read_text(encoding="utf-8"))
    print(json.dumps(score(data), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
