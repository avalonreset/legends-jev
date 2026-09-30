import copy
import datetime as dt
import io
import json
import os
import unittest
import urllib.error
from unittest.mock import patch
from legends_jev import core, provider
from legends_jev.cli import fixture_cases, materialize, main

def response(payload, choice="a"):
    levels = payload["questions"]["support"]["criteria"]
    return {"model": core.MODEL, "answers": {
        "action": {"type": "choice", "choice": choice, "confidence": 1., "probabilities": {k: float(k == choice) for k in payload["questions"]["action"]["criteria"]}},
        "insufficient": {"type": "noul", "noul": 0.},
        "support": {"type": "score", "score": 2., "confidence": 1., "legend": {str(i): v for i,v in enumerate(levels)}, "probabilities": {"0": 0., "1": 0., "2": 1.}}},
        "usage": {"input_tokens": 100, "output_tokens": 20}}

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.e = materialize(fixture_cases()[0])

    def test_valid_suggestion_is_never_actuation(self):
        result = core.decide(self.e, response)
        self.assertEqual(result["candidate_id"], "a")
        self.assertTrue(result["requires_operator_validation"])
        self.assertFalse(result["actuated"])

    def test_stale_blank_future_and_ineligible_skip_provider(self):
        for case in fixture_cases():
            if case["id"] in ("blank", "stale", "future", "unauthorized", "wrong-window", "disabled-only"):
                with self.subTest(case=case["id"]):
                    r = core.decide(materialize(case), lambda _: self.fail("provider called"))
                    self.assertEqual(r["status"], "operator_fallback")
                    self.assertFalse(r["provider_called"])

    def test_disabled_unauthorized_wrong_surface_removed(self):
        for field,value in (("enabled",False),("authorized",False),("surface_id","other")):
            e = copy.deepcopy(self.e)
            e["candidates"][0][field] = value
            p = core.request(e)
            self.assertNotIn("a", p["questions"]["action"]["criteria"])
            self.assertNotIn("surface_id", p["state"])

    def test_unknown_and_low_confidence_fallback(self):
        def low(p):
            r=response(p); r["answers"]["action"]["confidence"] = .79
            return r
        for transport in (lambda p: response(p,"unknown"), low):
            self.assertEqual(core.decide(self.e,transport)["status"],"operator_fallback")

    def test_malformed_responses_fallback(self):
        mutations = [lambda r: r.update(model="jev-latest"), lambda r:r.update(answers=[]),
            lambda r:r["answers"]["action"].update(choice="invented"),
            lambda r:r["answers"]["action"].update(confidence=float("nan")),
            lambda r:r["answers"]["action"].update(probabilities={"a":1}),
            lambda r:r["answers"]["support"].update(score=99),
            lambda r:r["answers"]["support"].update(legend={}),
            lambda r:r["answers"]["insufficient"].update(noul=True),
            lambda r:r.update(usage={"input_tokens":-1,"output_tokens":0})]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                def bad(p):
                    r=response(p); mutate(r); return r
                self.assertEqual(core.decide(self.e,bad)["status"],"operator_fallback")

    def test_untrusted_fields_rejected(self):
        for name,value in (("image","base64"),("command","execute"),("api_key","secret")):
            e=copy.deepcopy(self.e); e[name]=value
            with self.assertRaises(core.Invalid): core.validate(e)

    def test_private_scope_rejected(self):
        self.e["data_scope"]="private"
        with self.assertRaises(core.Invalid): core.validate(self.e)

    def test_candidate_flag_type_and_duplicate(self):
        self.e["candidates"][0]["authorized"]="true"
        with self.assertRaises(core.Invalid): core.validate(self.e)
        self.e=materialize(fixture_cases()[0]); self.e["candidates"][1]["id"]="a"
        with self.assertRaises(core.Invalid): core.validate(self.e)

    def test_timeout_fallback_single_attempt(self):
        with patch.object(provider.urllib.request,"build_opener") as opener, patch.dict(os.environ,{"TYPESAFE_API_KEY":"test-secret"}):
            opener.return_value.open.side_effect=TimeoutError("test-secret")
            r=core.decide(self.e,provider.call)
            self.assertEqual(r["reason"],"provider_network_or_timeout")
            self.assertEqual(opener.return_value.open.call_count,1)
            self.assertNotIn("test-secret",json.dumps(r))

    def test_missing_credential_is_not_a_provider_call(self):
        with patch.dict(os.environ,{},clear=True):
            result=core.decide(self.e,provider.call)
        self.assertEqual(result["reason"],"credential_not_provisioned")
        self.assertFalse(result["provider_called"])

    def test_http_errors_sanitized(self):
        for status in (301,401,429,500,529):
            with patch.object(provider.urllib.request,"build_opener") as opener, patch.dict(os.environ,{"TYPESAFE_API_KEY":"test-secret"}):
                opener.return_value.open.side_effect=urllib.error.HTTPError("https://secret",status,"secret",{},None)
                r=core.decide(self.e,provider.call)
                self.assertEqual(r["reason"],f"provider_http_{status}")
                self.assertNotIn("test-secret",json.dumps(r))

    def test_doctor_and_preview_benchmark_are_offline(self):
        with patch("legends_jev.cli.call",side_effect=AssertionError("network")), patch("sys.stdout",new_callable=io.StringIO):
            self.assertEqual(main(["doctor"]),0)
            self.assertEqual(main(["benchmark"]),0)
            self.assertEqual(main(["models"]),0)

    def test_direct_duplicate_abstains(self):
        e=materialize(next(c for c in fixture_cases() if c["id"]=="duplicate-match"))
        self.assertEqual(core.direct(e)["status"],"operator_fallback")

    def test_request_size_and_timestamp(self):
        self.e["evidence"]["text"]="x"*6001
        with self.assertRaises(core.Invalid): core.validate(self.e)
        self.e=materialize(fixture_cases()[0]); self.e["evidence"]["observed_at"]="2026-01-01"
        with self.assertRaises(core.Invalid): core.validate(self.e)

    def test_receipt_does_not_copy_evidence(self):
        self.e["evidence"]["text"]="unique-private-marker"
        self.assertNotIn("unique-private-marker",json.dumps(core.decide(self.e,response)))

    def test_json_field_type_matrix(self):
        invalid_values = [None, [], {}, True, 5]
        for value in invalid_values:
            for field in ("goal", "evidence", "candidates", "data_scope"):
                e=copy.deepcopy(self.e); e[field]=value
                with self.subTest(field=field,value=value), self.assertRaises(core.Invalid):
                    core.validate(e)
            for field in ("route", "description", "surface_id", "id"):
                e=copy.deepcopy(self.e); e["candidates"][0][field]=value
                with self.subTest(field=field,value=value), self.assertRaises(core.Invalid):
                    core.validate(e)

    def test_freshness_rechecked_after_provider(self):
        now=dt.datetime.now(dt.timezone.utc)
        self.e["evidence"]["observed_at"]=(now-dt.timedelta(seconds=119)).isoformat()
        ticks=iter([now,now+dt.timedelta(seconds=3)])
        class Clock(dt.datetime):
            @classmethod
            def now(cls,tz=None): return next(ticks)
        with patch.object(core.dt,"datetime",Clock):
            result=core.decide(self.e,response)
        self.assertEqual(result["reason"],"stale_or_future_evidence")
        self.assertEqual(result["status"],"operator_fallback")

    def test_redirects_rejected(self):
        self.assertIsNone(provider.NoRedirect().redirect_request(None,None,302,"",{},"https://other.example"))

    def test_invalid_json_sanitized(self):
        with patch.object(provider.urllib.request,"build_opener") as opener, patch.dict(os.environ,{"TYPESAFE_API_KEY":"test-secret"}):
            opener.return_value.open.return_value.__enter__.return_value.read.return_value=b"test-secret not json"
            r=core.decide(self.e,provider.call)
            self.assertEqual(r["reason"],"provider_invalid_json")
            self.assertNotIn("test-secret",json.dumps(r))

    def test_unknown_provider_fields_not_logged(self):
        def extra(p):
            r=response(p)
            r["answers"]["action"]["debug"]="test-secret"
            r["usage"]["debug"]="test-secret"
            return r
        self.assertNotIn("test-secret",json.dumps(core.decide(self.e,extra)))

if __name__=="__main__": unittest.main()
