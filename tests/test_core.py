import base64
import copy
import datetime as dt
import io
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
import urllib.error
from unittest.mock import patch
import zlib
from legends_jev import core, provider
from legends_jev.cli import fixture_cases, materialize, main


def minimal_png_bytes(width=400, height=300):
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + ihdr + b"\x00\x00\x00\x00"


def valid_rgb_png_bytes(width=400, height=300, color=(40, 90, 160)):
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    row = b"\x00" + bytes(color) * width
    compressed = zlib.compress(row * height, level=1)
    def chunk(ctype, cdata):
        crc = zlib.crc32(ctype + cdata) & 0xFFFFFFFF
        return struct.pack(">I", len(cdata)) + ctype + cdata + struct.pack(">I", crc)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")


def response(payload, choice="a"):
    levels = payload["questions"]["support"]["criteria"]
    ans = {
        "action": {"type": "choice", "choice": choice, "confidence": 1., "probabilities": {k: float(k == choice) for k in payload["questions"]["action"]["criteria"]}},
        "insufficient": {"type": "noul", "noul": 0.},
        "support": {"type": "score", "score": 2., "confidence": 1., "legend": {str(i): v for i, v in enumerate(levels)}, "probabilities": {"0": 0., "1": 0., "2": 1.}},
    }
    if "target_visible" in payload["questions"]:
        ans["target_visible"] = {"type": "noul", "noul": 0.96}
    if "target_box" in payload["questions"]:
        ans["target_box"] = {"type": "box", "box": {"top": 0.25, "bottom": 0.75, "left": 0.25, "right": 0.75}, "confidence": 0.92}
    return {"model": core.MODEL, "answers": ans, "usage": {"input_tokens": 100, "output_tokens": 20}}


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
        for field, value in (("enabled", False), ("authorized", False), ("surface_id", "other")):
            e = copy.deepcopy(self.e)
            e["candidates"][0][field] = value
            p = core.request(e)
            self.assertNotIn("a", p["questions"]["action"]["criteria"])
            self.assertNotIn("surface_id", p["state"])

    def test_unknown_and_low_confidence_fallback(self):
        def low(p):
            r = response(p)
            r["answers"]["action"]["confidence"] = .79
            return r
        for transport in (lambda p: response(p, "unknown"), low):
            self.assertEqual(core.decide(self.e, transport)["status"], "operator_fallback")

    def test_malformed_responses_fallback(self):
        mutations = [lambda r: r.update(model="jev-latest"), lambda r: r.update(answers=[]),
            lambda r: r["answers"]["action"].update(choice="invented"),
            lambda r: r["answers"]["action"].update(confidence=float("nan")),
            lambda r: r["answers"]["action"].update(probabilities={"a": 1}),
            lambda r: r["answers"]["support"].update(score=99),
            lambda r: r["answers"]["support"].update(legend={}),
            lambda r: r["answers"]["insufficient"].update(noul=True),
            lambda r: r.update(usage={"input_tokens": -1, "output_tokens": 0})]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                def bad(p):
                    r = response(p)
                    mutate(r)
                    return r
                self.assertEqual(core.decide(self.e, bad)["status"], "operator_fallback")

    def test_untrusted_fields_rejected(self):
        for name, value in (("image", "base64"), ("command", "execute"), ("api_key", "secret")):
            e = copy.deepcopy(self.e)
            e[name] = value
            with self.assertRaises(core.Invalid):
                core.validate(e)

    def test_private_scope_rejected(self):
        self.e["data_scope"] = "private"
        with self.assertRaises(core.Invalid):
            core.validate(self.e)

    def test_candidate_flag_type_and_duplicate(self):
        self.e["candidates"][0]["authorized"] = "true"
        with self.assertRaises(core.Invalid):
            core.validate(self.e)
        self.e = materialize(fixture_cases()[0])
        self.e["candidates"][1]["id"] = "a"
        with self.assertRaises(core.Invalid):
            core.validate(self.e)

    def test_timeout_fallback_single_attempt(self):
        with patch.object(provider.urllib.request, "build_opener") as opener, patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-secret"}):
            opener.return_value.open.side_effect = TimeoutError("test-secret")
            r = core.decide(self.e, provider.call)
            self.assertEqual(r["reason"], "provider_network_or_timeout")
            self.assertEqual(opener.return_value.open.call_count, 1)
            self.assertNotIn("test-secret", json.dumps(r))

    def test_missing_credential_is_not_a_provider_call(self):
        with patch.dict(os.environ, {}, clear=True):
            result = core.decide(self.e, provider.call)
        self.assertEqual(result["reason"], "credential_not_provisioned")
        self.assertFalse(result["provider_called"])

    def test_http_errors_sanitized(self):
        for status in (301, 401, 429, 500, 529):
            with patch.object(provider.urllib.request, "build_opener") as opener, patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-secret"}):
                opener.return_value.open.side_effect = urllib.error.HTTPError("https://secret", status, "secret", {}, None)
                r = core.decide(self.e, provider.call)
                self.assertEqual(r["reason"], f"provider_http_{status}")
                self.assertNotIn("test-secret", json.dumps(r))

    def test_doctor_and_preview_benchmark_are_offline(self):
        with patch("legends_jev.cli.call", side_effect=AssertionError("network")), patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(main(["doctor"]), 0)
            self.assertEqual(main(["benchmark"]), 0)
            self.assertEqual(main(["models"]), 0)

    def test_direct_duplicate_abstains(self):
        e = materialize(next(c for c in fixture_cases() if c["id"] == "duplicate-match"))
        self.assertEqual(core.direct(e)["status"], "operator_fallback")

    def test_request_size_and_timestamp(self):
        self.e["evidence"]["text"] = "x" * 6001
        with self.assertRaises(core.Invalid):
            core.validate(self.e)
        self.e = materialize(fixture_cases()[0])
        self.e["evidence"]["observed_at"] = "2026-01-01"
        with self.assertRaises(core.Invalid):
            core.validate(self.e)

    def test_receipt_does_not_copy_evidence(self):
        self.e["evidence"]["text"] = "unique-private-marker"
        self.assertNotIn("unique-private-marker", json.dumps(core.decide(self.e, response)))

    def test_json_field_type_matrix(self):
        invalid_values = [None, [], {}, True, 5]
        for value in invalid_values:
            for field in ("goal", "evidence", "candidates", "data_scope"):
                e = copy.deepcopy(self.e)
                e[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(core.Invalid):
                    core.validate(e)
            for field in ("route", "description", "surface_id", "id"):
                e = copy.deepcopy(self.e)
                e["candidates"][0][field] = value
                with self.subTest(field=field, value=value), self.assertRaises(core.Invalid):
                    core.validate(e)

    def test_freshness_rechecked_after_provider(self):
        now = dt.datetime.now(dt.timezone.utc)
        self.e["evidence"]["observed_at"] = (now - dt.timedelta(seconds=119)).isoformat()
        ticks = iter([now, now + dt.timedelta(seconds=3)])
        class Clock(dt.datetime):
            @classmethod
            def now(cls, tz=None):
                return next(ticks)
        with patch.object(core.dt, "datetime", Clock):
            result = core.decide(self.e, response)
        self.assertEqual(result["reason"], "stale_or_future_evidence")
        self.assertEqual(result["status"], "operator_fallback")

    def test_redirects_rejected(self):
        self.assertIsNone(provider.NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.example"))

    def test_invalid_json_sanitized(self):
        with patch.object(provider.urllib.request, "build_opener") as opener, patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-secret"}):
            opener.return_value.open.return_value.__enter__.return_value.read.return_value = b"test-secret not json"
            r = core.decide(self.e, provider.call)
            self.assertEqual(r["reason"], "provider_invalid_json")
            self.assertNotIn("test-secret", json.dumps(r))

    def test_unknown_provider_fields_not_logged(self):
        def extra(p):
            r = response(p)
            r["answers"]["action"]["debug"] = "test-secret"
            r["usage"]["debug"] = "test-secret"
            return r
        self.assertNotIn("test-secret", json.dumps(core.decide(self.e, extra)))

    def test_image_dimension_and_format_guards(self):
        fmt, w, h = core.inspect_image_bytes(minimal_png_bytes(800, 600))
        self.assertEqual((fmt, w, h), ("png", 800, 600))
        with self.assertRaises(core.Invalid):
            core.inspect_image_bytes(minimal_png_bytes(200, 300))
        with self.assertRaises(core.Invalid):
            core.inspect_image_bytes(minimal_png_bytes(1600, 600))
        with self.assertRaises(core.Invalid):
            core.inspect_image_bytes(minimal_png_bytes(400, 400) + b"acTL")

    def test_auto_image_normalization_and_pixel_box_mapping(self):
        # 1. Oversized 1920x1080 desktop screenshot auto-scales to 1568x882
        raw_1080p = valid_rgb_png_bytes(1920, 1080)
        entry_1080p = core.prepare_image_bytes(raw_1080p, normalize=True)
        self.assertTrue(entry_1080p["normalized"])
        self.assertEqual((entry_1080p["original_width"], entry_1080p["original_height"]), (1920, 1080))
        self.assertEqual((entry_1080p["width"], entry_1080p["height"]), (1568, 882))
        px_1080p = core.pixel_box({"left": 0.25, "top": 0.5, "right": 0.75, "bottom": 0.75}, entry_1080p)
        self.assertAlmostEqual(px_1080p["left"], 480, delta=2)
        self.assertAlmostEqual(px_1080p["right"], 1440, delta=2)
        self.assertAlmostEqual(px_1080p["top"], 540, delta=2)
        self.assertAlmostEqual(px_1080p["bottom"], 810, delta=2)
        self.assertAlmostEqual(px_1080p["center_x"], 960, delta=2)

        # 2. Undersized 160x80 button crop auto-pads onto 280x280 canvas
        raw_crop = valid_rgb_png_bytes(160, 80)
        entry_crop = core.prepare_image_bytes(raw_crop, normalize=True)
        self.assertTrue(entry_crop["normalized"])
        self.assertEqual((entry_crop["width"], entry_crop["height"]), (280, 280))
        self.assertEqual((entry_crop["pad_left"], entry_crop["pad_top"]), (60, 100))
        # Center of 280x280 canvas (0.5, 0.5) maps to center of 160x80 crop (80, 40)
        px_crop = core.pixel_box({"left": 60 / 280, "top": 100 / 280, "right": 220 / 280, "bottom": 180 / 280}, entry_crop)
        self.assertEqual((px_crop["left"], px_crop["top"], px_crop["right"], px_crop["bottom"]), (0, 0, 160, 80))
        self.assertEqual((px_crop["center_x"], px_crop["center_y"]), (80, 40))

    def test_general_purpose_ocr_and_visual_grounding(self):
        entry = core.prepare_image_bytes(valid_rgb_png_bytes(1920, 1080), normalize=True)
        images = {"screen": entry}
        payload = core.ocr_request(
            "Verify invoice header and locate the Pay Now button",
            images,
            expect_texts=["Invoice #1042", "Balance Due"],
            locate_targets=["screen:the Pay Now button"],
            choices={"payable": "Invoice shows Balance Due and an active Pay Now button", "paid": "Invoice is already marked Paid"},
        )
        self.assertTrue(provider.uses_images(payload))
        self.assertIn("text_0", payload["questions"])
        self.assertIn("text_1", payload["questions"])
        self.assertIn("locate_0_box", payload["questions"])
        self.assertIn("classification", payload["questions"])

        def mock_ocr_transport(p):
            return {
                "model": core.MODEL,
                "answers": {
                    "goal_supported": {"type": "noul", "noul": 0.97},
                    "readability": {
                        "type": "score",
                        "score": 1.95,
                        "confidence": 0.96,
                        "legend": {str(i): v for i, v in enumerate(p["questions"]["readability"]["criteria"])},
                        "probabilities": {"0": 0.0, "1": 0.05, "2": 0.95},
                    },
                    "text_0": {"type": "noul", "noul": 0.99},
                    "text_1": {"type": "noul", "noul": 0.94},
                    "locate_0_visible": {"type": "noul", "noul": 0.98},
                    "locate_0_box": {
                        "type": "box",
                        "box": {"top": 0.5, "bottom": 0.6, "left": 0.4, "right": 0.6},
                        "confidence": 0.91,
                    },
                    "classification": {
                        "type": "choice",
                        "choice": "payable",
                        "confidence": 0.96,
                        "probabilities": {"payable": 0.96, "paid": 0.02, "unknown": 0.02},
                    },
                },
                "usage": {"input_tokens": 1400, "output_tokens": 80},
            }

        receipt = core.inspect_ocr(
            "Verify invoice header and locate the Pay Now button",
            images,
            mock_ocr_transport,
            expect_texts=["Invoice #1042", "Balance Due"],
            locate_targets=["screen:the Pay Now button"],
            choices={"payable": "Invoice shows Balance Due and an active Pay Now button", "paid": "Invoice is already marked Paid"},
        )
        self.assertEqual(receipt["schema"], "legends-jev/ocr-receipt-v1")
        self.assertEqual(receipt["status"], "suggestion")
        self.assertEqual(receipt["choice"], "payable")
        self.assertTrue(all(m["present"] for m in receipt["text_matches"]))
        self.assertEqual(len(receipt["locations"]), 1)
        loc = receipt["locations"][0]
        self.assertTrue(loc["visible"])
        self.assertAlmostEqual(loc["pixel_box"]["center_x"], 960, delta=2)
        self.assertAlmostEqual(loc["pixel_box"]["center_y"], 594, delta=2)

        # CLI preview test for ocr subcommand with auto-normalization
        with tempfile.TemporaryDirectory() as tmp:
            img_path = Path(tmp) / "screen.png"
            img_path.write_bytes(valid_rgb_png_bytes(1920, 1080))
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                rc = main([
                    "ocr",
                    "--goal", "Check button",
                    "--image", f"screen={img_path}",
                    "--expect-text", "Submit",
                    "--locate", "the Submit button",
                ])
            self.assertEqual(rc, 0)
            out = json.loads(buf.getvalue())
            self.assertTrue(out["preview"])
            self.assertTrue(out["image_dimensions"]["screen"]["normalized"])
            self.assertEqual(out["image_dimensions"]["screen"]["original_width"], 1920)
            self.assertEqual(out["image_dimensions"]["screen"]["width"], 1568)

    def test_decide_with_optical_image_grounding(self):
        e = copy.deepcopy(self.e)
        e["evidence"]["kind"] = "optical-image"
        e["evidence"]["images"] = {"screen": core.prepare_image_bytes(valid_rgb_png_bytes(1000, 800))}
        res = core.decide(e, response)
        self.assertEqual(res["status"], "suggestion")
        self.assertEqual(res["candidate_id"], "a")
        self.assertEqual(res["target_pixel_box"]["center_x"], 500)
        self.assertEqual(res["target_pixel_box"]["center_y"], 400)

    def test_signage_optical_recognition_and_box_validation(self):
        b64 = base64.b64encode(minimal_png_bytes(800, 600)).decode("ascii")
        images = {"streetview": {"format": "png", "data_base64": b64}}
        payload = core.signage_request("DeSano Pizzeria Napoletana", ["Pizzeria Napoletana"], images)
        self.assertTrue(provider.uses_images(payload))
        def mock_transport(p):
            return {
                "model": core.MODEL,
                "answers": {
                    "sign_visible": {"type": "noul", "noul": 0.99},
                    "suspect_terms_shown": {"type": "noul", "noul": 0.98},
                    "best_image": {
                        "type": "choice",
                        "choice": "streetview",
                        "confidence": 0.95,
                        "probabilities": {"streetview": 0.95, "none": 0.05},
                    },
                    "sign_box": {
                        "type": "box",
                        "box": {"top": 0.2, "bottom": 0.4, "left": 0.3, "right": 0.8},
                        "confidence": 0.85,
                    },
                    "verdict": {
                        "type": "choice",
                        "choice": "supports_full_title",
                        "confidence": 0.99,
                        "probabilities": {
                            "supports_full_title": 0.99,
                            "omits_suspect_terms": 0.01,
                            "obstructed_or_no_sign": 0.0,
                        },
                    },
                },
                "usage": {"input_tokens": 1800, "output_tokens": 90},
            }
        res = core.inspect_signage("DeSano Pizzeria Napoletana", ["Pizzeria Napoletana"], images, mock_transport)
        self.assertEqual(res["status"], "suggestion")
        self.assertEqual(res["verdict"], "supports_full_title")
        self.assertEqual(res["best_image"], "streetview")
        self.assertEqual(res["sign_box"], {"top": 0.2, "bottom": 0.4, "left": 0.3, "right": 0.8})
        self.assertEqual(res["sign_pixel_box"]["center_x"], 440)
        self.assertEqual(res["sign_pixel_box"]["center_y"], 180)
        # Inverted box coordinates must fall back safely
        def bad_box(p):
            r = mock_transport(p)
            r["answers"]["sign_box"]["box"]["left"] = 0.9
            return r
        self.assertEqual(core.inspect_signage("DeSano", ["Pizza"], images, bad_box)["status"], "operator_fallback")


if __name__ == "__main__":
    unittest.main()
