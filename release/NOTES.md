# `legends-jev v0.1.0`

An MIT-licensed decision adapter for TypeSafe Jev. It compares explicitly
supplied action candidates against small text observations and returns reviewed
suggestions or an operator fallback.

- Text-only Choice, Score and Noul helpers with strict response validation.
- Offline previews and deterministic freshness/eligibility guards.
- Explicit single-request API calls, sanitized errors and no automatic retries.
- Portable environment credentials and a Windows DPAPI pilot wrapper.
- Labeled synthetic comparison and packaged operator recipe.

This release does not capture screens, ground images, click controls or navigate
browsers. Operators validate results and use their existing action tools. The
hosted Jev service is separate from the open-source adapter. See the benchmark
report for observed performance and limits; no general speedup is claimed.
