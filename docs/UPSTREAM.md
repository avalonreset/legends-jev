# Upstream verification

Checked 2026-09-29 against official TypeSafe documentation (URLs fetched live).

- [Models](https://docs.typesafe.ai/models): current version `jev-1.13.0`,
  text-only input, no image/audio/video input. Aliases can move. Published input
  rate is $0.042 per million tokens; outputs free. Receipt estimates use this
  dated rate, not a billing guarantee.
- [API](https://docs.typesafe.ai/api): `/v1/systemone` evaluates supplied state
  and typed questions; returns Choice, Score and Noul answers. This adapter fixes
  its endpoint, pins the response model and validates every used answer field.
- [Confidence](https://docs.typesafe.ai/confidence): confidence describes the
  answer distribution; it is not an operational correctness guarantee.
- [Official skill](https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md)
  and [documentation index](https://docs.typesafe.ai/llms.txt) were inspected.
  Function-call and skill-suggestion cookbook titles describe downstream
  integrations, not proof of native browser or desktop actuation.

No upstream visual grounding or actuation interface was established. The
adapter deliberately consumes only text and returns advice. Hosted service
terms and account retention entitlements are separate from this adapter's MIT
license. No private-data retention entitlement is assumed.
