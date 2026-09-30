# `legends-jev`

Typed decision advice for an operator choosing application or browser actions.
Supply a small text observation and explicit candidate actions. Get a candidate
ID or an operator fallback, with validated Choice, Score and Noul answers.

Jev is a hosted, text-only TypeSafe model. This MIT-licensed adapter is open
source; the hosted model is not distributed here. No screenshot capture, image
grounding, desktop connection, browser navigation or action execution is provided.
Existing `legends-shell-kit` and `legends-chrome-kit` retain actuation. The
operator must check the live target, evidence freshness, scope and permissions.

## Install and use

Python 3.10+; no runtime dependencies. Install this source into an isolated
environment, or install the reviewed wheel. Do not register a separate agent
skill. The byte-exact central `cto-legends` skill is vendored in `skills/`.

```sh
python -m venv .venv
# Windows: .venv/Scripts/python.exe; POSIX: .venv/bin/python
.venv/Scripts/python.exe -m pip install .
.venv/Scripts/python.exe -m legends_jev doctor
.venv/Scripts/python.exe -m legends_jev guide
.venv/Scripts/python.exe -m legends_jev sample
```

Save `sample` output to a new JSON file, inspect it, then:

```sh
python -m legends_jev readiness --input evidence.json
python -m legends_jev preview --input evidence.json
python -m legends_jev direct --input evidence.json
python -m legends_jev decide --input evidence.json --execute --output receipt.json
```

Use the isolated Python, not an arbitrary global Python. `decide` without
`--execute` only previews. Doctor, sample, preview, readiness, direct and guide
are offline. `models --execute` and `decide --execute` make one network request
each (decision preflight can skip it). `benchmark --execute` runs at most 20
synthetic cases sequentially and stops on the first provider/protocol failure.
It compares an exact-match code baseline with Jev, not with timed Astra reasoning.

## Credentials and data

Provision `TYPESAFE_API_KEY` through your shell's secret manager/environment.
Do not put values in commands, source, `.env` commits, logs or prompts. On
Windows `scripts/Invoke-Jev.ps1 -Python <isolated-python> <args>` reuses the
existing user's DPAPI pilot credential only for `--execute`; it restores the
previous environment and clears unmanaged plaintext memory afterward. No
credential is copied or rotated. Other machines must provision their own env.

Only reviewed synthetic, public or nonsecret app metadata is in scope. Explicit
fields exclude binaries, image payload fields, arbitrary commands and provider
URLs. Free text is not a secret detector: redact before submitting. The module
does not discover, capture, scrape or upload local application content itself.
Receipts omit input text and store a hash plus validated answers. Preview prints
the actual proposed text request for operator review. Never publish unreviewed
previews or receipts. Account retention/ZDR entitlement is not established.

## Routing and limits

Routinely consider this helper when computer use, application control or browser
work contains a repeated semantic choice over short supplied evidence. Prefer
ordinary code for exact matches. Prefer the reasoning operator when a one-off
choice already has enough context, or the evidence is ambiguous. Consideration
does not mean every click needs a network call.

Input is bounded to 16KB, eight candidates and 6,000 evidence characters.
Observations older than 120 seconds, over five seconds in the future, empty
evidence and no eligible candidates return fallback without a call. Disabled,
unauthorized and wrong-surface candidates are excluded. Flags are operator
assertions, not independently verified permissions. Inputs inside evidence are
untrusted; prompt instructions are not a security proof.

Model `jev-1.13.0` is pinned and verified in every response. One 30-second
timeout, no redirects, no automatic retries, no alias fallback and no plan
changes. Malformed responses, unavailable credentials, network errors, unknowns
and conservative uncertainty gates return operator fallback. Thresholds are
pilot review triggers, not calibrated safety guarantees. No result authorizes
an action. See [operator recipe](legends_jev/docs/recipe.md),
[upstream findings](docs/UPSTREAM.md), and [release plan](release/RELEASE.md).

## Development

```sh
python -m unittest discover -s tests -v
python -m build
```

The distribution contains plain recipes and synthetic fixtures, not an
attachable vault. Local evidence belongs in ignored `var/` or a user-selected
output directory. Public catalog admission follows the independent module
release and immutable-source verification; local guide registration is distinct
from a public managed install.
