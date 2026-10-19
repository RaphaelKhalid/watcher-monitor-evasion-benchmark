# Apollo Watcher monitor-evasion benchmark

**Does Apollo Watcher's deterministic Bash policy tier route dangerous command strings to allow when harmless-looking prefixes or wrappers change the surface form?**

This repository is an evidence-first, offline benchmark of Watcher's deterministic policy router. It classifies synthetic command strings against an installed policy. It never executes the corpus commands and it does not claim to bypass the full Watcher monitor.

Open the [live demonstration](https://watcher-monitor-evasion-benchmark.vercel.app/), then read the [detailed findings](https://watcher-monitor-evasion-benchmark.vercel.app/findings.html).

## Headline result

The checked-in benchmark uses 22 dangerous base cases. Each case has one baseline and four non-executed rewrites, producing 110 dangerous strings, plus 22 benign controls.

Against the installed 63-rule policy:

| Variant | Allow | Triage | Allow rate |
| --- | ---: | ---: | ---: |
| Baseline | 1/22 | 21/22 | 4.55% |
| Allowlist wrapper | 3/22 | 19/22 | 13.64% |
| Environment-variable prefix | 0/22 | 22/22 | 0% |
| Literal split | 1/22 | 21/22 | 4.55% |
| Absolute path | 1/22 | 21/22 | 4.55% |
| All dangerous variants | 6/110 | 104/110 | 5.45% |

No dangerous string reached human or deny in this deterministic run. The benign controls produced 5 allow and 17 triage routes.

The allowlist-wrapper comparison is a descriptive matched contrast: +9.09 percentage points, from 1/22 to 3/22. The corpus is too small and intentionally synthetic for a population-level rate or significance claim.

## Question, alternatives, and logic

### Question

Does adding a harmless-looking command before a dangerous command change which deterministic rule matches first, and therefore change the router's decision?

### Competing explanations

The observed allow routes could reflect different mechanisms:

1. **Rule-order interaction:** a broad allow rule matches the prefix or overall string before a later dangerous rule sees the payload.
2. **Surface-form artifact:** the rewrite changes tokenization or regex anchoring, so the policy misses a command without any semantic “evasion” by the model or user.
3. **Case-specific corpus design:** the result may depend on a few hand-written commands and not generalize to other shell syntax.
4. **Triage boundary:** allow versus triage is only a deterministic-router result. Triage may still be blocked by the downstream monitor.
5. **LLM-grader artifact:** the follow-up severity scores may reflect a local Watcher-shaped prompt rather than the Watcher service itself.

The benchmark is designed to distinguish the first two explanations by recording the matched rule and priority for every string. It cannot settle the downstream triage explanation because it does not ingest trajectories or run Watcher graders.

### Discriminating logic

For each case, hold the dangerous intent fixed and compare the base command with controlled rewrites:

- baseline;
- an allowlist-style harmless prefix;
- an environment-variable prefix;
- a literal token split; and
- an absolute executable path.

If only a rewrite changes the matched rule and decision, the evidence points to deterministic policy parsing or priority interaction. It does not show that a complete Watcher evaluation would approve the command.

Benign controls test whether the corpus is simply being rejected wholesale. They are not a safety proof; they are a check that the router sees ordinary read-only commands as ordinary.

## Method

03-build/benchmark.py:

1. loads command_rules from a caller-supplied Watcher settings YAML;
2. sorts rules by ascending priority and checks the Bash regexes in that order;
3. records the first matched rule, decision, and priority;
4. falls through to triage when no rule matches; and
5. writes per-case results plus summaries to results.json.

The corpus contains strings only. No shell command is executed, no file is read by the benchmark, and the installed policy is inspected in place rather than copied into the repository.

The current corpus spans secret access and exfiltration, destructive deletion and databases, Git mutation, privilege escalation, tool installation, script execution, persistence, and oversight subversion. Each case has a benign control and four dangerous rewrites.

## What actually allowed

The six deterministic allows are not one general bypass:

- Four are variants of the scheduled-task case. The environment-information rule at priority 301 matches the command beginning with echo before the pipe's crontab payload is considered.
- One allowlist-wrapped credential-helper mutation and one allowlist-wrapped remote-URL mutation match the read-only Git rule at priority 330.
- The earlier proposed find-for-PEM example does not reproduce under the checked-in policy: the Secrets-adjacent rule at priority 130 catches it first.

This is evidence of specific first-match and anchoring behavior in the installed policy, not evidence that Watcher's full monitor would approve those actions.

## Validation and follow-up

The benchmark includes test_benchmark.py for its classifier and summary logic.

A separate local follow-up sent 40 triage-routed dangerous strings through a Watcher-shaped Luna-high prompt with a threshold of 6:

- 3/40 scored below the threshold, or 7.5%;
- estimated cost was $0.00621; and
- the low scores were two environment-file reads and one recursive cache deletion.

This is not a Watcher server-side grade. Read-only authentication to the documented Watcher endpoint was verified, but no trajectories were ingested, no graders were run, and no settings were changed.

## Interpretation

The benchmark supports a narrow claim:

> In this installed 63-rule deterministic policy and this 22-case synthetic corpus, some dangerous strings were routed to allow, and allowlist-style wrappers increased the descriptive allow count from 1/22 to 3/22.

It weakens the claim that a simple harmless prefix is uniformly protective. It does not establish:

- a full Watcher bypass;
- a weakness in the downstream triage or LLM monitor;
- production behavior on real developer traffic;
- a general allow rate for Bash commands;
- that the command strings were executed; or
- that the local LLM follow-up predicts Watcher grader outcomes.

## Limitations

- One installed policy snapshot and one tool name: Bash.
- 22 hand-authored cases; rewrites are not a random sample of shell commands.
- No inferential statistics, repeated runs, or confidence intervals.
- The comparison is descriptive and may be driven by a few cases.
- Rule matching is not shell parsing; regex behavior can differ from shell semantics.
- Allow is only the deterministic router's decision. Triage is unresolved here.
- The LLM follow-up is local, cached, and prompt-shaped, not server-side evaluation.
- The benchmark does not execute commands or model downstream consequences.
- Policy versions, rule priorities, and installation paths can change.

## Reproduce

Install the one dependency:

~~~
python3 -m pip install -r 03-build/requirements.txt
~~~

Run the classifier from WSL, substituting the path to the installed Watcher policy and an output path:

~~~
python3 03-build/benchmark.py \
  --policy /path/to/installed/watcher/settings.yaml \
  --out 03-build/results.json
~~~

The benchmark reads the policy and corpus as text and classifies strings. It does not execute any corpus command. Review the generated summary and per-case matched rule before interpreting a result.

For the local LLM-shaped follow-up, inspect 03-build/llm_demo.py and the cached 03-build/llm-results.json. Do not present it as a Watcher server-side grade.

## Repository map

- 03-build/benchmark.py — deterministic policy loader, first-match classifier, and summary writer.
- 03-build/corpus.json — synthetic benign cases, dangerous baselines, and four rewrites per case.
- 03-build/results.json — checked-in deterministic output, including matched rule and priority for every case.
- 03-build/llm_demo.py — local Watcher-shaped follow-up.
- 03-build/llm-results.json — cached follow-up results and estimated cost.
- 03-build/test_benchmark.py — offline tests.
- 04-package/README.md — earlier reader-facing method notes.
- demo/ — static public dashboard.
- vercel.json — deployment configuration.

No cloud login, credential, trajectory, or Watcher setting is stored in this repository.