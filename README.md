# ![legends-jev](assets/banner.webp)

[![release](https://img.shields.io/github/v/release/avalonreset/legends-jev?label=release&sort=date&style=flat-square&labelColor=000000&color=ff0000)](https://github.com/avalonreset/legends-jev/releases/latest)
[![checks](https://img.shields.io/github/actions/workflow/status/avalonreset/legends-jev/checks.yml?branch=main&label=checks&style=flat-square&labelColor=000000)](https://github.com/avalonreset/legends-jev/actions/workflows/checks.yml)
[![license](https://img.shields.io/github/license/avalonreset/legends-jev?label=license&style=flat-square&labelColor=000000&color=666666)](LICENSE)

Typed decision advice, general-purpose optical recognition (`ocr`), and storefront
signage verification (`signage`) for an operator choosing application, browser,
document, or local SEO review actions. Supply a small text observation and
explicit candidate actions, or supply PNG/JPEG screenshots, documents, or photos
to get validated Choice, Score, Noul, and Box answers (including original-image
`pixel_box` coordinates).

Jev (`jev-1.14.0`) is a hosted TypeSafe System One model. This MIT-licensed adapter
is open source; the hosted model is not distributed here. No screen capture,
desktop connection, browser navigation or action execution is provided.
The operator must check the live target, evidence freshness, scope and permissions.

## Agent setup (via `cto-legends`)

Part of the [CTO Legends](https://github.com/avalonreset/cto-legends) ecosystem. `cto-legends` is the only registered skill; this repo vendors a pinned copy at `skills/cto-legends/SKILL.md`.

Install with `cto-legends install legends-jev`, then follow the module recipe the router loads. Do not register this module as its own skill.

## Quick start: install and use

With [`cto-legends`](https://github.com/avalonreset/cto-legends) installed:

```sh
cto-legends sync
cto-legends sync --apply
cto-legends install legends-jev
cto-legends install legends-jev --apply
cto-legends handoff legends-jev
cto-legends run legends-jev -- doctor
```

The preview commands do not install or call TypeSafe.

Python 3.11+ with `Pillow>=10.0.0` for local image normalization and bounding-box geometry.
Install this source into an isolated environment, or install the reviewed wheel.
Do not register a separate agent skill. The byte-exact central `cto-legends`
skill is vendored in `skills/`.

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

For general-purpose OCR text verification, visual target localization (`box` +
`pixel_box`), and visual state classification over 1 to 4 PNG/JPEG images:

```sh
python -m legends_jev ocr \
  --goal "Verify invoice status and locate the Pay Now button" \
  --image screen=invoice.png \
  --expect-text "Invoice #1042" \
  --expect-text "Balance Due" \
  --locate "screen:the Pay Now button" \
  --choice "payable=Invoice shows Balance Due and an active Pay Now button" \
  --choice "paid=Invoice is already marked Paid" \
  --execute
```

For Google Business Profile and Street View signage verification (used by
[`legends-geogrid`](https://github.com/avalonreset/legends-geogrid) when installed):

```sh
python -m legends_jev signage \
  --title "DeSano Pizzeria Napoletana" \
  --suspect-term "Pizzeria Napoletana" \
  --image streetview=streetview.jpg \
  --image logo=logo.jpg \
  --execute
```

Use the isolated Python, not an arbitrary global Python. `decide`, `ocr`, and
`signage` without `--execute` only preview the request offline. Doctor, sample,
preview, readiness, direct and guide are offline. `models --execute`,
`decide --execute`, `ocr --execute`, and `signage --execute` make one network
request each (decision preflight can skip it). `benchmark --execute` runs at
most 20 synthetic cases sequentially and stops on the first provider/protocol
failure. It compares an exact-match code baseline with Jev, not with timed Astra
reasoning.

## Credentials and data

Provision `TYPESAFE_API_KEY` through your shell's secret manager/environment, or
pass an explicit `--api-key-file <path>` (symlinks refused). Do not put secret
values in commands, source, `.env` commits, logs or prompts.

Only reviewed synthetic, public or nonsecret app metadata is in scope. Free text
and screenshots are not secret detectors: redact before submitting. The module
does not discover, capture, scrape or upload local application content itself.
Receipts omit input text and image bytes and store a hash plus validated answers.
Preview prints the proposed structure (with image byte sizes instead of raw base64)
for operator review. Never publish unreviewed previews or receipts. Account
retention/ZDR entitlement is not established.

## Routing, OCR fortification, and limits

Routinely consider this helper when computer use, application control, browser
work, document checks, or local SEO audits need a fast (~150-250ms) structured
choice, optical text check, or bounding-box coordinate lookup over short supplied
evidence or 1 to 4 images. Prefer ordinary code for exact string matches. Prefer
the reasoning operator when a one-off choice already has enough context, or the
evidence is ambiguous. Consideration does not mean every click needs a network call.

Text input is bounded to 16KB, eight candidates and 6,000 evidence characters.
Observations older than 120 seconds, over five seconds in the future, empty
evidence and no eligible candidates return fallback without a call. Disabled,
unauthorized and wrong-surface candidates are excluded. Flags are operator
assertions, not independently verified permissions. Inputs inside evidence and
images are untrusted; prompt instructions are not a security proof.

Model `jev-1.14.0` is pinned and verified in every response. One 30-second
timeout, no redirects, no automatic retries, no alias fallback and no plan
changes. For optical workflows (`ocr`, `signage`, and `decide` with `evidence.images`),
TypeSafe requires still PNG/JPEG images within `280..1568` pixels per side.
`load_image_entry` and `prepare_image_bytes` automatically normalize out-of-range
screenshots (such as `1920x1080` desktops or small crops) into `280..1568` px
(unless `--no-normalize` is passed), send `assets` with header
`TypeSafe-Danger-Zone-Images: true`, validate `box` (`top`, `bottom`, `left`,
`right`), `noul`, `score`, and `choice` fields, and map normalized `0..1` boxes
back to exact original-image pixel coordinates (`pixel_box` with `left`, `top`,
`right`, `bottom`, `center_x`, `center_y`). Malformed responses, unavailable
credentials, network errors, unknowns and conservative uncertainty gates return
operator fallback. Thresholds are pilot review triggers, not calibrated safety
guarantees. No result authorizes an action. See [operator recipe](legends_jev/docs/recipe.md),
[agent recipe](docs/AGENT-RECIPE.md), and [upstream findings](docs/UPSTREAM.md).

## Development

```sh
python scripts/check_release.py
python -m unittest discover -s tests -v
python -m build
python scripts/check_wheel.py
```

The distribution contains plain recipes and synthetic fixtures, not an
attachable vault. Local evidence belongs in ignored `var/` or a user-selected
output directory. Public catalog admission follows the independent module
release and immutable-source verification; local guide registration is distinct
from a public managed install.

## Architecture and project layout

```text
Operator / Agent
  -> Offline preflight & image normalization (280..1568 px per side)
  -> Explicit preview (`preview`, `decide`, `ocr`, `signage` without `--execute`)
  -> Single TypeSafe `jev-1.14.0` request (only when `--execute` is passed)
  -> Validated Choice, Score, Noul, and Box (`pixel_box` mapped to original image)
```

- `legends_jev/`: Python 3.11+ with `Pillow>=10.0.0` for local image normalization and bounding-box geometry across structured decision, OCR, and signage verification workflows.
- `legends_jev/docs/recipe.md` and `docs/`: Operator recipe, [agent recipe](docs/AGENT-RECIPE.md), [upstream notes](docs/UPSTREAM.md), and [search strategy](docs/SEARCH-STRATEGY.md).
- `skills/cto-legends/SKILL.md`: Pinned copy of the central [`cto-legends`](https://github.com/avalonreset/cto-legends) router skill.

## FAQ

**Does `legends-jev` click buttons or control my desktop directly?**
No. `legends-jev` returns validated `Choice`, `Score`, `Noul`, and `Box` (`pixel_box`) observations. Desktop and browser actuation remain in [`legends-shell`](https://github.com/avalonreset/legends-shell) or your chosen automation tool.

**What happens if I pass a 1920x1080 screenshot to `legends-jev ocr`?**
`legends-jev` automatically normalizes out-of-range PNG/JPEG images into TypeSafe's required `280..1568` pixel bounds before sending the request and maps returned `0..1` bounding boxes back to exact `pixel_box` coordinates on your original screenshot.

## License and contributing

MIT licensed. See [LICENSE](LICENSE), [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), [CONTRIBUTING.md](CONTRIBUTING.md), [SUPPORT.md](SUPPORT.md), and [SECURITY.md](SECURITY.md).

---

**Specification & benchmarks on cto-legends.com:**
- **Module specification & architecture matrix:** [cto-legends.com/modules/legends-jev](https://cto-legends.com/modules/legends-jev)
- **Related engineering dispatches:** [Browser Automation AI: Computer Use Agent Benchmarks](https://cto-legends.com/blog?post=browser-automation-ai-computer-use-benchmarks) · [How to Build AI Agents: Production CLI & MCP Routing](https://cto-legends.com/blog?post=how-to-build-ai-agents-cli-mcp-routing) · [Claude Code Skills: MCP vs CLI Workflow Architecture](https://cto-legends.com/blog?post=claude-code-skills-mcp-vs-cli-workflow)
- **Ecosystem hub:** [cto-legends.com/home](https://cto-legends.com/home)
