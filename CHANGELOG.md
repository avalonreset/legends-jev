# Changelog

## 0.2.1 - 2026-10-29

- Raise minimum supported Python runtime to Python 3.11 (`requires-python = ">=3.11"`) across package metadata, documentation, and multi-OS CI.
- Harden `.github/workflows/checks.yml` with 40-character commit SHA action pins, explicit `contents: read` permissions, and `pip>=26.2.2` before package installation.

## 0.2.0 - 2026-10-21

- Upgrade default pinned model to `jev-1.14.0` (released 2026-10-14).
- Add general-purpose `ocr` CLI subcommand and Python API (`ocr_request`, `inspect_ocr`) for optical text verification (`--expect-text`), visual target localization (`--locate`), readability scoring, and state classification (`--choice`) returning `legends-jev/ocr-receipt-v1`.
- Add automatic image dimension normalization (`prepare_image_bytes`, `load_image_entry`) to scale/pad out-of-range screenshots (such as `1920x1080` desktops or small crops) into TypeSafe's required `280..1568` px range and map returned `box` coordinates back to exact original-image pixel coordinates (`pixel_box` with `left`, `top`, `right`, `bottom`, `center_x`, `center_y`).
- Add `signage` CLI subcommand and `inspect_signage` Python helper for bounded storefront, Street View, and logo verification (`legends-jev/signage-receipt-v1`).
- Support optional optical grounding (`evidence.images` / `kind: "optical-image"`) in `decide` envelopes while preserving 100% compatibility with existing text-only `legends-jev/evidence-v1` workflows, offline preview defaults, DPAPI wrapper, and operator fallback guarantees.

## 0.1.0 - 2026-09-30

- Bounded typed action advice from supplied text evidence.
- Deterministic eligibility/freshness guards and explicit operator fallback.
- Safe environment provisioning and optional Windows DPAPI wrapper.
- Offline doctor, preview, direct baseline, labeled synthetic benchmark.
- Central router recipe, local-guide discovery and public catalog release plan.
