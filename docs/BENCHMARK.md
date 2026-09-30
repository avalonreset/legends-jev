# Initial synthetic benchmark

Run date: 2026-09-29 local (2026-09-30 UTC). Pinned model: `jev-1.13.0`.
Twenty cases and expected labels were written before the first call; the
rubric and thresholds were not adjusted after observing these results.

| Route | Cases | Final label agreement | Suggestions | Wrong suggestions | Fallbacks | Median decision latency |
|---|---:|---:|---:|---:|---:|---:|
| Direct exact-match code | 20 | 13/20 | 1 | 0 | 19 | 0.0315 ms |
| Jev with local guards | 20 | 17/20 | 5 | 0 | 15 | 217.057 ms |

Six Jev-path cases were rejected locally without an API call. Fourteen
explicit calls completed; latency above includes zero-latency preflight rows.
Among actual calls, median latency was 229.001 ms, mean 230.353 ms and range
200.526 to 278.925 ms. Total input usage was 7,816 tokens, an estimated
$0.000328272 at the published dated rate, not a billing reconciliation.
All eight positive raw Choice answers selected the intended candidate, but
three were held by the insufficiency/support gates. Those abstentions are
counted as label mismatches, not quietly counted as successful suggestions.
The three were exact settings selection, evidence containing a hostile embedded
directive, and reading a completed-job status. Twelve negative cases correctly
ended in fallback, including ambiguity, contradictions, unavailable controls,
stale timestamps and ineligible targets.

This small authored set demonstrates plumbing and bounded behavior. It is not
a representative computer-use benchmark or a security evaluation. Labels and
implementation were authored by the same operator. Zero wrong suggestions in
five suggestions is very weak evidence for unseen inputs. The direct route is
ordinary exact-match code, not Astra/Gemini reasoning. Operator review time,
real actuation success and end-to-end savings were not measured. For the exact
case, code is both faster and less conservative; use it first.

Recommendation: routinely consider Jev for repeated semantic candidate
comparisons, retain direct code and operator fallback, and gather task-specific
labels before expanding scope. Keep conservative gates unchanged until a
separate held-out evaluation justifies a change. No desktop was touched for
this benchmark.

The fixture is packaged at `legends_jev/data/cases.json`; the local unedited
receipt is `var/benchmark-live-v1.json`. Public artifacts contain synthetic
fixtures and this summary, not the private host receipt path or credentials.
