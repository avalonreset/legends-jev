import argparse
import datetime as dt
import importlib.resources as resources
import json
import os
from pathlib import Path
import statistics
from . import __version__
from .core import Invalid, decide, direct, preflight, request, validate
from .provider import call

def read(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(16001)
    if len(raw) > 16000:
        raise Invalid("Input file exceeds 16KB")
    try:
        return json.loads(raw)
    except (ValueError, UnicodeError):
        raise Invalid("Input file is not valid JSON") from None

def fixture_cases():
    return json.loads(resources.files("legends_jev").joinpath("data/cases.json").read_text(encoding="utf-8"))

def materialize(case):
    obj = json.loads(json.dumps(case["input"]))
    timestamp = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=case.get("age_seconds", 0))
    obj["evidence"]["observed_at"] = timestamp.isoformat()
    return obj

def benchmark(execute=False):
    rows = []
    for case in fixture_cases():
        envelope = materialize(case)
        baseline = direct(envelope)
        row = {"id": case["id"], "expected": case["expected"], "direct": baseline}
        if execute:
            row["jev"] = decide(envelope, call)
        rows.append(row)
        if execute and row["jev"]["reason"].startswith(("provider_", "credential_", "Unexpected", "Invalid", "Response", "Inconsistent")):
            break
    summary = {}
    for route in ("direct", "jev") if execute else ("direct",):
        results = [r[route] for r in rows]
        matches = sum((r[route]["candidate_id"] or "unknown") == r["expected"] for r in rows)
        suggested = [r for r in rows if r[route]["status"] == "suggestion"]
        summary[route] = {"cases": len(rows), "label_matches": matches, "suggestions": len(suggested),
            "wrong_suggestions": sum(r[route]["candidate_id"] != r["expected"] for r in suggested),
            "fallbacks": len(rows)-len(suggested), "mean_latency_ms": statistics.mean(r["latency_ms"] for r in results),
            "median_latency_ms": statistics.median(r["latency_ms"] for r in results),
            "provider_calls": sum(r.get("provider_called", False) for r in results)}
    return {"fixture_version": "1", "synthetic_only": True, "completed": len(rows) == len(fixture_cases()),
        "baseline": "Deterministic unique exact goal/description match; not a timed Astra comparison",
        "operator_review_time_measured": False, "summary": summary, "results": rows}

def main(argv=None):
    parser = argparse.ArgumentParser(description="legends-jev: advice only over supplied text evidence")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    sub.add_parser("guide")
    sub.add_parser("sample")
    for name in ("preview", "decide", "direct", "readiness"):
        p = sub.add_parser(name)
        p.add_argument("--input", required=True)
        p.add_argument("--output")
        if name == "decide":
            p.add_argument("--execute", action="store_true")
    for name in ("models", "benchmark"):
        p = sub.add_parser(name)
        p.add_argument("--execute", action="store_true")
        p.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        if getattr(args, "output", None) and Path(args.output).exists():
            raise Invalid("Output exists; choose a new receipt")
        if args.command == "guide":
            print(resources.files("legends_jev").joinpath("docs/recipe.md").read_text(encoding="utf-8"))
            return 0
        if args.command == "doctor":
            cases = fixture_cases()
            for case in cases:
                validate(materialize(case))
            result = {"module": "legends-jev", "version": __version__, "offline_ok": True,
                "fixture_cases": len(cases), "credential_env_present": bool(os.environ.get("TYPESAFE_API_KEY")),
                "provider_verified": False, "actuation": False, "visual_grounding": False}
        elif args.command == "sample":
            result = materialize(fixture_cases()[0])
        elif args.command == "models":
            if not args.execute:
                result = {"preview": True, "endpoint": "GET /v1/models", "provider_called": False}
            else:
                raw = call()
                # Model listing contains only provider model metadata.
                result = {"provider_called": True, "models": raw}
        elif args.command == "benchmark":
            result = benchmark(args.execute)
        else:
            envelope = read(args.input)
            reason = preflight(envelope)
            if args.command == "readiness":
                result = {"input_ready": reason is None, "reason": reason, "credential_env_present": bool(os.environ.get("TYPESAFE_API_KEY")), "provider_verified": False}
            elif args.command == "direct":
                result = direct(envelope)
            elif args.command == "decide" and args.execute:
                result = decide(envelope, call)
            else:
                payload = request(envelope)
                result = {"preview": True, "provider_called": False, "preflight_reason": reason, "request": payload}
        serialized = json.dumps(result, indent=2, allow_nan=False)
        if getattr(args, "output", None):
            with Path(args.output).open("x", encoding="utf-8") as stream:
                stream.write(serialized + "\n")
            print(json.dumps({"receipt": str(args.output), "written": True}))
        else:
            print(serialized)
        return 0
    except (Invalid, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    except OSError:
        print(json.dumps({"ok": False, "error": "local_file_access_failed"}))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
