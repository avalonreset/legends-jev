# `legends-jev` operator recipe

Select this helper for repeated semantic action selection from supplied screen
descriptions, accessibility text, app metadata, or screenshots (`decide`), for
general-purpose optical text verification, visual target localization, and state
classification (`ocr`), or for fast optical verification of storefront/Street View/logo
images (`signage`) using `jev-1.14.0` with `TypeSafe-Danger-Zone-Images: true`.
Routinely consider it in computer use, application control, browser tasks,
document/UI OCR checks, and local SEO visual signage verification. It never
captures screens or executes actions.

1. Read `cto-legends` capabilities and `handoff legends-jev`. A local-guide
   handoff is not a managed public installation. Resolve the documented local
   runtime or manager `status`, then run `python -m legends_jev doctor`.
2. Collect the smallest relevant nonsecret text or image evidence through an
   authorized existing tool. Preserve target/surface identity locally. For
   `decide`, supply goal, capture time, candidate IDs/descriptions/routes and
   operator-verified eligibility (`sample` shows the envelope shape; optional
   `evidence.images` adds optical `target_box` and `target_pixel_box` grounding).
3. For general-purpose OCR and visual grounding on 1 to 4 PNG/JPEG images, use
   `ocr --goal ... --image label=path` with any combination of:
   - `--expect-text "<string>"` (1..12 expected text strings verified via `noul`)
   - `--locate "[label:]<target>"` (1..4 targets localized via `noul` + `box`,
     returning both `0..1` coordinates and original-image `pixel_box` with
     `center_x`, `center_y`)
   - `--choice "key=description"` (1..8 classifications plus automatic `unknown`)
   Out-of-bounds images (such as `1920x1080` desktop screenshots or small button
   crops) are automatically normalized into TypeSafe's `280..1568` px range and
   mapped back to original pixel coordinates.
4. For storefront and logo verification against a Google Business Profile title
   (used by `legends-geogrid`), run `signage --title ... --suspect-term ... --image label=path`.
5. Run without `--execute` first to preview the structured request offline.
   Provision `TYPESAFE_API_KEY` safely or use the supplied Windows DPAPI wrapper
   (`scripts/Invoke-Jev.ps1 -Python <isolated-python> ...`). An existing
   authorized task may cover explicit execution; do not add a redundant prompt.
6. Passing `--execute` performs at most one call. Inspect `status`, `reason`,
   typed answers, `pixel_box` coordinates, and `latency_ms`. Missing keys,
   provider failure, stale evidence and uncertain answers return `operator_fallback`.
   Stop a failed batch; do not retry blindly or invent a provider decision.
7. Validate suggestions against current evidence and permissions, especially if
   the UI changed. Reobserve after actuation. Use `legends-shell-kit` for native
   controls or `legends-chrome-kit` for browser actions. Jev never actuates.

All suggestions require operator review even with high confidence. Default
thresholds are conservative pilot settings, not calibrated safety guarantees.
No account-wide budget enforcement is claimed.

## Bounded helpers

- **`decide`** (`legends-jev/receipt-v1`): Returns a closed candidate `choice`,
  an insufficiency `noul`, a three-level support `score`, and (when
  `evidence.images` is supplied) `target_visible`, `target_box`, and
  `target_pixel_box`.
- **`ocr`** (`legends-jev/ocr-receipt-v1`): Returns `goal_supported` (`noul`),
  `readability_score` (`score` 0..2), `text_matches` (per-string `present_noul`),
  `locations` (visibility-gated `box` + original-image `pixel_box`), and optional
  `choice`.
- **`signage`** (`legends-jev/signage-receipt-v1`): Returns `verdict`
  (`supports_full_title`, `omits_suspect_terms`, `obstructed_or_no_sign`),
  `best_image`, `sign_visible`, `suspect_terms_shown`, `sign_box`, and
  `sign_pixel_box`.
