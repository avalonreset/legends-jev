# Changelog

## 0.2.5 - 2026-11-21

- Add `scripts/render_cards.py` and render 7 outlined Legends Font `r1` architecture, plain-english workflow, comparison, agent handoff, message desk, and star-shrine SVG cards under `assets/cards/r1/`.
- Rewrite `README.md` with visual architecture cards, explicit `280..1568` px in-process normalization and `pixel_box` coordinate reversal documentation, collapsible reference drawers, and evergreen ecosystem links.
- Include `assets/cards/r1/*.svg` in `MANIFEST.in` and enforce SVG card presence, XML/dash hygiene, and `CITATION.cff` version parity in `scripts/check_release.py`.

## 0.2.4 - 2026-11-11

- Harden image loading and decompression against CWE-409 / CWE-400 bombs: bound initial file reads before allocation, enforce `MAX_IMAGE_DIMENSION = 16384` and `MAX_IMAGE_PIXELS = 25000000` in `parse_image_header()`, bound `zlib.decompressobj().decompress(..., expected + 1)` in `_decode_simple_png_rgb()`, and catch Pillow decompression-bomb and parse exceptions as sanitized `Invalid` errors.
- Prevent `TYPESAFE_API_KEY` header injection and exception leakage (CWE-209 / CWE-93): validate resolved API keys against printable ASCII (`^[\x21-\x7e]{1,512}$`) and catch `http.client.HTTPException` (`InvalidHeader`, `BadStatusLine`, `IncompleteRead`, `LineTooLong`) in `provider.py`.
- Enforce ancestor-chain symlink refusal (`refuse_symlink_tree`) across `--input`, `--image`, `--api-key-file`, and `--output`, and add explicit `--overwrite` support for `--output`.
- Isolate untrusted `--expect-text` and `--locate` values in `ocr_request()` inside `state.expected_texts` and `state.locate_targets` so question instructions remain static strings.
- Align `docs/AGENT-RECIPE.md`, `README.md`, `legends_jev/docs/recipe.md`, `pyproject.toml` (`license-files`), `CITATION.cff`, and `scripts/check_release.py` (`REQUIRED` list).

## 0.2.3 - 2026-11-05

- Eliminate Windows Defender / EDR Law 1 and Law 3 triggers: remove the legacy Windows DPAPI credential helper (`_windows_dpapi_key`) from `legends_jev/provider.py` and remove the legacy PowerShell credential wrapper script. Read `TYPESAFE_API_KEY` strictly from the environment or an explicit `--api-key-file <path>` with `is_symlink()` refusal.
- Remove duplicate `VERSION` and candidate release directory so `pyproject.toml` (`0.2.3`) is the single authoritative version source matching `legends_jev/__init__.py` and `CHANGELOG.md`.
- Add `docs/AGENT-RECIPE.md`, `THIRD_PARTY_NOTICES.md`, `assets/manifest.json`, and `scripts/check_release.py` Gold Standard offline release verification gate, and fix the `README.md` checks badge URL (`actions/workflows/checks.yml`) and dependency description (`Python 3.11+ with Pillow>=10.0.0 for local image normalization and bounding-box geometry`).

## 0.2.2 - 2026-11-04

- Add `Pillow>=10.0.0` to package `dependencies` in `pyproject.toml` and remove the Windows PowerShell `System.Drawing` image-resizing subprocess fallback from `legends_jev/core.py`, eliminating child PowerShell process creation during JPEG/PNG normalization.
- Report `credential_present` in `doctor` and `readiness` (`legends_jev/cli.py`) so agents detect provisioned credentials directly without invoking wrapper scripts.

## 0.2.1 - 2026-10-29

- Raise minimum supported Python runtime to Python 3.11 (`requires-python = ">=3.11"`) across package metadata, documentation, and multi-OS CI.
- Harden `.github/workflows/checks.yml` with 40-character commit SHA action pins, explicit `contents: read` permissions, and `pip>=26.2.2` before package installation.

## 0.2.0 - 2026-10-21

- Upgrade default pinned model to `jev-1.14.0` (released 2026-10-14).
- Add general-purpose `ocr` CLI subcommand and Python API (`ocr_request`, `inspect_ocr`) for optical text verification (`--expect-text`), visual target localization (`--locate`), readability scoring, and state classification (`--choice`) returning `legends-jev/ocr-receipt-v1`.
- Add automatic image dimension normalization (`prepare_image_bytes`, `load_image_entry`) to scale/pad out-of-range screenshots (such as `1920x1080` desktops or small crops) into TypeSafe's required `280..1568` px range and map returned `box` coordinates back to exact original-image pixel coordinates (`pixel_box` with `left`, `top`, `right`, `bottom`, `center_x`, `center_y`).
- Add `signage` CLI subcommand and `inspect_signage` Python helper for bounded storefront, Street View, and logo verification (`legends-jev/signage-receipt-v1`).
- Support optional optical grounding (`evidence.images` / `kind: "optical-image"`) in `decide` envelopes while preserving 100% compatibility with existing text-only `legends-jev/evidence-v1` workflows, offline preview defaults, and operator fallback guarantees.

## 0.1.0 - 2026-09-30

- Bounded typed action advice from supplied text evidence.
- Deterministic eligibility/freshness guards and explicit operator fallback.
- Safe environment provisioning.
- Offline doctor, preview, direct baseline, labeled synthetic benchmark.
- Central router recipe and local-guide discovery.
