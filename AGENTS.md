# `legends-jev` agent rules

Start with [docs/AGENT-RECIPE.md](docs/AGENT-RECIPE.md), [README.md](README.md), [legends_jev/docs/recipe.md](legends_jev/docs/recipe.md), and [skills/cto-legends/SKILL.md](skills/cto-legends/SKILL.md).

## Core Operating Rules

1. **Single Router Skill**: Discovery belongs to `skills/cto-legends/SKILL.md`. Do not register this module as a separate skill or insert unpublished catalog pins.
2. **Readiness First**: Run `legends-jev doctor` (or `python -m legends_jev doctor`) offline before live use. Use only the chosen isolated Python runtime.
3. **No Capture or Actuation**: Never add screen capture, browser connection, or input actuation to this typed decision and optical recognition adapter.
4. **Bounded Nonsecret Inputs**: Do not send private secrets, credentials, full accessibility trees, or unreviewed screenshots. Keep source and provider calls bounded, and preserve operator validation and fallback.

## EDR and Security Guardrails

- **No Hidden Console Spawning or Bypass Wrappers**: Never spawn hidden consoles, execution-policy bypass shell wrappers, or child PowerShell image/credential scripts. All image normalization runs in-process via pure Python and `Pillow`.
- **No Browser Profile or DPAPI Credential Scanning**: Never read or scan local browser profile databases, DPAPI stores, or third-party credential files. Read `TYPESAFE_API_KEY` strictly from the environment or an explicit `--api-key-file <path>` (which refuses symlinks).
- **Fail-Closed Single-File I/O**: Input files, image paths, `--api-key-file`, and `--output` paths refuse target and non-system ancestor symlinks (`is_symlink()`), and `--output` refuses existing files unless `--overwrite` is explicitly passed.

Run `python scripts/check_release.py` and `python -m unittest discover -s tests -v`, build wheel and sdist, and run `python scripts/check_wheel.py` before release.
