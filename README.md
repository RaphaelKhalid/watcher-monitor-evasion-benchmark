# Apollo Watcher monitor-evasion benchmark

An evidence-first red-team benchmark for the deterministic policy layer of [Apollo Watcher](https://github.com/ApolloResearch/watcher).

Open the [live demonstration](https://watcher-monitor-evasion-benchmark.vercel.app/), then read the [detailed findings](https://watcher-monitor-evasion-benchmark.vercel.app/findings.html). The main page shows one reproduced failure and a server-side Watcher triage response; the findings page contains the full offline benchmark.

## Current result

Against the installed 63-rule policy, 110 dangerous command strings produced 6 `allow` routes and 104 `triage` routes. Direct baselines hit `allow` 1/22 times (4.55%); allowlist-wrapped variants hit it 3/22 times (13.64%), a +9.09 percentage-point lift. A Luna-high, Watcher-shaped follow-up graded 40 triage-routed strings: 3 scored below the threshold of 6 (7.5%) at an estimated $0.00621.

This is a narrow router finding, not a claim that the full Watcher monitor is bypassed. The benchmark never executes a corpus command.

## Contents

- `03-build/`: policy parser, synthetic corpus, tests, raw results, and cached LLM-tier output.
- `04-package/`: reader-facing method and limitation notes.
- `demo/`: static public results dashboard.
- `decisions.md`: experiment log and kill-pass corrections.
