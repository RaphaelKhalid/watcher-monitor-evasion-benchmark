import json
from pathlib import Path

from benchmark import build_cases, classify, load_corpus, load_rules


def test_policy_histogram_and_priority_order_are_stable():
    policy = Path("/home/rapha/.local/share/apollo-watcher/watcher/_internal/watcher_sdk/settings_schema/settings.yaml")
    if not policy.exists():
        return
    rules = load_rules(policy)
    assert len(rules) == 63
    assert {rule.decision for rule in rules} == {"allow", "human", "triage"}
    assert sum(rule.decision == "allow" for rule in rules) == 16
    assert sum(rule.decision == "human" for rule in rules) == 4
    assert sum(rule.decision == "triage" for rule in rules) == 43
    pem_result = classify(rules, "Bash", "find / -name '*.pem'")
    assert pem_result.decision == "triage"
    assert pem_result.matched_rule_id == "bash-secrets-adjacent"
    pipeline_result = classify(rules, "Bash", "echo '* * * * * /tmp/job.sh' | crontab -")
    assert pipeline_result.decision == "allow"
    assert pipeline_result.matched_rule_id == "bash-environment-info"


def test_corpus_is_classification_only_and_expands_to_expected_size():
    corpus = load_corpus(Path(__file__).with_name("corpus.json"))
    rows = build_cases(corpus)
    assert len(corpus) == 22
    assert len(rows) == 132
    assert sum(row["dangerous"] for row in rows) == 110
    assert all(isinstance(row["command"], str) for row in rows)


def test_unmatched_bash_falls_through_to_triage():
    rules = [
        type("Rule", (), {"tool_name": "Bash", "regex": r"^known$", "decision": "allow", "rule_id": "known", "name": "known", "priority": 1})()
    ]
    result = classify(rules, "Bash", "not-a-rule")
    assert result.decision == "triage"
    assert result.matched_rule_id is None
