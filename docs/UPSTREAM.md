# Upstream verification

Checked 2026-10-21 against official TypeSafe documentation (URLs fetched live).

- [Models](https://docs.typesafe.ai/models): current version `jev-1.14.0` (released 2026-10-14) alongside `jev-1.13.0`. Aliases (`jev-latest`, `jev-preview`) can move. Published input rate is $0.042 per million tokens; outputs free. Receipt estimates use this dated rate, not a billing guarantee.
- [Images](https://docs.typesafe.ai/images) and [Box](https://docs.typesafe.ai/primitives/box): `POST /v1/systemone` accepts still PNG/JPEG images (`280..1568` px per side) via `assets` and evaluates `box` bounding-box questions on `jev-1.14.0` when header `TypeSafe-Danger-Zone-Images: true` is sent.
- [API](https://docs.typesafe.ai/api): `/v1/systemone` evaluates supplied state and typed questions; returns Choice, Score, Noul and Box answers. This adapter fixes its endpoint, pins the response model and validates every used answer field.
- [Confidence](https://docs.typesafe.ai/confidence): confidence describes the answer distribution; it is not an operational correctness guarantee.
- [Official skill](https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md) and [documentation index](https://docs.typesafe.ai/llms.txt) were inspected. Function-call and skill-suggestion cookbook titles describe downstream integrations, not proof of native browser or desktop actuation.

The adapter consumes supplied text or explicitly validated PNG/JPEG evidence and returns advice only. Hosted service terms and account retention entitlements are separate from this adapter's MIT license. No private-data retention entitlement is assumed.
