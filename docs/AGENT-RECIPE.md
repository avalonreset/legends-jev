# Operating legends-jev

This is an on-demand module recipe, not a registered skill. The central `cto-legends` router owns discovery (`skills/cto-legends/SKILL.md`).

## Readiness

1. Run `legends-jev doctor` (or `python -m legends_jev doctor`). This is offline, free, validates all 20 packaged synthetic fixtures, and reports whether `TYPESAFE_API_KEY` is configured (`credential_env_present` / `credential_present`).
2. Credentials are read strictly from the `TYPESAFE_API_KEY` environment variable or an explicit `--api-key-file <path>` (which refuses symlinks). Never echo API keys to terminal output, logs, or receipts.
3. All provider-capable commands (`decide`, `ocr`, `signage`, `models`, `benchmark`) preview offline by default (`preview: true`, `provider_called: false`). Passing `--execute` sends at most one HTTPS request per call (or up to 20 sequential synthetic cases for `benchmark --execute`).

## CLI and Python Workflow Reference

Top-level flags: `legends-jev [--version] [--api-key-file FILE] <command> ...`

| Goal | CLI Command | Python API | Notes |
|---|---|---|---|
| Offline readiness check | `legends-jev [--api-key-file FILE] doctor [--api-key-file FILE]` | `validate()`, `credential_present()` | Offline `0` exit; validates 20 synthetic cases and reports credential readiness |
| Print operator guide | `legends-jev guide` | `importlib.resources` (`docs/recipe.md`) | Prints the packaged Markdown operator recipe |
| Emit sample envelope | `legends-jev sample` | `fixture_cases()[0]` | Outputs a valid `legends-jev/evidence-v1` JSON envelope with current UTC timestamp |
| Check envelope readiness | `legends-jev readiness --input FILE [--output FILE] [--overwrite] [--api-key-file FILE]` | `preflight(envelope)` | Offline check of envelope schema, freshness (`-5..120s`), and candidate eligibility |
| Preview decision payload | `legends-jev preview --input FILE [--output FILE] [--overwrite] [--api-key-file FILE]` | `request(envelope)` | Offline preview of the compiled `jev-1.14.0` System One request |
| Deterministic baseline | `legends-jev direct --input FILE [--output FILE] [--overwrite] [--api-key-file FILE]` | `direct(envelope)` | Offline unique exact-match baseline without calling TypeSafe |
| Typed action advice | `legends-jev decide --input FILE [--execute] [--output FILE] [--overwrite] [--api-key-file FILE]` | `decide(envelope, call)` | Returns `legends-jev/receipt-v1` (`choice`, `noul`, `score`, optional `target_pixel_box`) |
| General-purpose OCR & boxes | `legends-jev ocr --goal "..." --image label=path [--expect-text "..."] [--locate "..."] [--choice k=desc] [--no-normalize] [--api-key-file FILE] [--execute] [--output FILE] [--overwrite]` | `ocr_request(...)`, `inspect_ocr(...)` | Returns `legends-jev/ocr-receipt-v1` with text matches, `0..1` boxes, and original-image `pixel_box` |
| Storefront signage check | `legends-jev signage --title "..." --suspect-term "..." --image label=path [--no-normalize] [--api-key-file FILE] [--execute] [--output FILE] [--overwrite]` | `signage_request(...)`, `inspect_signage(...)` | Returns `legends-jev/signage-receipt-v1` (`supports_full_title`, `omits_suspect_terms`, `obstructed_or_no_sign`) |
| Inspect provider models | `legends-jev models [--api-key-file FILE] [--execute] [--output FILE] [--overwrite]` | `call()` | Previews `GET /v1/models` offline; `--execute` queries live model metadata |
| Synthetic benchmark | `legends-jev benchmark [--api-key-file FILE] [--execute] [--output FILE] [--overwrite]` | `benchmark(execute=...)` | Runs 20 synthetic cases (`direct` offline; adds `jev` when `--execute` is passed) |

## EDR and Security Guardrails

1. **Zero Hidden Consoles or Bypass Wrappers**: Never spawn hidden consoles, execution-policy bypass shell wrappers, or background localhost daemons. Do not use or create `.ps1`, `.bat`, `.cmd`, `.vbs`, or `.ahk` wrapper scripts. Image normalization runs strictly in-process via pure Python and `Pillow`.
2. **Strict Environment or Explicit Key-File Credential Loading**: Never read local browser profile databases, DPAPI stores, or third-party credential stores. Supply `TYPESAFE_API_KEY` strictly via the environment or an explicit `--api-key-file <path>` (which enforces target and ancestor `is_symlink()` refusal and a 4 KB size bound).
3. **Zero Secret or Raw Evidence Exposure**: Never print `TYPESAFE_API_KEY` values to stdout, logs, or Markdown receipts. Receipts omit raw evidence text and base64 image bytes, recording only `input_sha256` and validated answers.
4. **No Implicit Capture or Actuation**: `legends-jev` is a pure decision and optical recognition adapter (`actuation: false`). It never captures screens, connects to browsers, or synthesizes keyboard/mouse input.
5. **Fail-Closed Single-File Output**: `--output <path>` refuses target and ancestor symlinks (`is_symlink()`) and refuses existing files by default unless `--overwrite` is explicitly passed.
