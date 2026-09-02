#!/usr/bin/env python3
"""Offline Watcher deterministic-tier benchmark.

This tool classifies command strings only. It never executes corpus commands.
The policy is read from a caller-supplied YAML path so the installed Watcher
policy can be inspected in WSL without copying its internal files.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - friendly CLI error
    raise SystemExit("Missing dependency: install PyYAML with `python -m pip install pyyaml`") from exc


@dataclass(frozen=True)
class Rule:
    rule_id: str
    tool_name: str
    name: str
    regex: str
    decision: str
    priority: int


@dataclass(frozen=True)
class Classification:
    decision: str
    matched_rule_id: str | None
    matched_rule_name: str | None
    priority: int | None


def load_rules(policy_path: Path) -> list[Rule]:
    data = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    raw_rules = data.get("command_rules", {}).get("rules", [])
    rules: list[Rule] = []
    for raw in raw_rules:
        rules.append(
            Rule(
                rule_id=raw["id"],
                tool_name=raw["tool_name"],
                name=raw.get("name", raw["id"]),
                regex=raw["regex"],
                decision=raw["decision"],
                priority=int(raw["priority"]),
            )
        )
    return sorted(rules, key=lambda rule: (rule.priority, rule.rule_id))


def classify(rules: list[Rule], tool: str, command: str) -> Classification:
    for rule in rules:
        if rule.tool_name != tool:
            continue
        try:
            matched = re.search(rule.regex, command) is not None
        except re.error as exc:
            raise ValueError(f"Invalid regex in {rule.rule_id}: {exc}") from exc
        if matched:
            return Classification(rule.decision, rule.rule_id, rule.name, rule.priority)
    # The deterministic tier is a router. An unmatched command falls through
    # to the triage model rather than being treated as allowed.
    return Classification("triage", None, None, None)


def load_corpus(corpus_path: Path) -> list[dict[str, Any]]:
    data = json.loads(corpus_path.read_text(encoding="utf-8"))
    return data["cases"]


def build_cases(corpus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in corpus:
        rows.append({"case_id": case["id"], "category": case["category"], "variant": "benign", "command": case["benign"], "dangerous": False})
        rows.append({"case_id": case["id"], "category": case["category"], "variant": "baseline", "command": case["dangerous"], "dangerous": True})
        for variant, command in case["rewrites"].items():
            rows.append({"case_id": case["id"], "category": case["category"], "variant": variant, "command": command, "dangerous": True})
    return rows


def summarize(rows: list[dict[str, Any]], rules: list[Rule]) -> dict[str, Any]:
    dangerous = [row for row in rows if row["dangerous"]]
    benign = [row for row in rows if not row["dangerous"]]
    decisions = Counter(row["decision"] for row in dangerous)
    benign_decisions = Counter(row["decision"] for row in benign)
    policy_decisions = Counter(rule.decision for rule in rules)
    by_variant: dict[str, dict[str, Any]] = {}
    for variant in sorted({row["variant"] for row in dangerous}):
        subset = [row for row in dangerous if row["variant"] == variant]
        counts = Counter(row["decision"] for row in subset)
        by_variant[variant] = {
            "total": len(subset),
            "decisions": dict(sorted(counts.items())),
            "allow_rate": round(counts.get("allow", 0) / len(subset), 4) if subset else 0.0,
            "strong_route_rate": round((counts.get("human", 0) + counts.get("deny", 0)) / len(subset), 4) if subset else 0.0,
        }
    by_category: dict[str, dict[str, int]] = defaultdict(dict)
    for category in sorted({row["category"] for row in dangerous}):
        counts = Counter(row["decision"] for row in dangerous if row["category"] == category)
        by_category[category] = dict(sorted(counts.items()))
    return {
        "dangerous_total": len(dangerous),
        "decision_histogram": dict(sorted(decisions.items())),
        "benign_total": len(benign),
        "benign_decision_histogram": dict(sorted(benign_decisions.items())),
        "policy_rule_decision_histogram": dict(sorted(policy_decisions.items())),
        "allow_shortcut_rate": round(decisions.get("allow", 0) / len(dangerous), 4) if dangerous else 0.0,
        "strong_route_rate": round((decisions.get("human", 0) + decisions.get("deny", 0)) / len(dangerous), 4) if dangerous else 0.0,
        "by_variant": by_variant,
        "by_category": dict(by_category),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, required=True, help="Path to Watcher's installed settings.yaml")
    parser.add_argument("--corpus", type=Path, default=Path(__file__).with_name("corpus.json"))
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("results.json"))
    args = parser.parse_args()

    rules = load_rules(args.policy)
    rows = []
    for row in build_cases(load_corpus(args.corpus)):
        result = classify(rules, "Bash", row["command"])
        rows.append({**row, **asdict(result)})
    report = {
        "tool": "Bash",
        "policy_path": str(args.policy),
        "rule_count": len(rules),
        "corpus_path": str(args.corpus),
        "summary": summarize(rows, rules),
        "cases": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rules": len(rules), **report["summary"]}, indent=2))
    print(f"Wrote raw results to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
