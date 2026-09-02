# Apollo Watcher monitor-evasion benchmark

An evidence-first red-team benchmark for the deterministic policy layer of [Apollo Watcher](https://github.com/ApolloResearch/watcher).

Open the live demo at the deployed URL, or run the offline benchmark from `03-build/README.md`.

## Current result

Against the installed 63-rule policy, 110 dangerous command strings produced 6 `allow` routes and 104 `triage` routes. Direct baselines hit `allow` 1/22 times (4.55%); allowlist-wrapped variants hit it 3/22 times (13.64%), a +9.09 percentage-point lift.

This is a narrow router finding, not a claim that the full Watcher monitor is bypassed. The benchmark never executes a corpus command.

## Contents

- `03-build/`: policy parser, synthetic corpus, tests, and raw results.
- `04-package/`: reader-facing method and limitation notes.
- `demo/`: static public results dashboard.
- `decisions.md`: experiment log and kill-pass corrections.
