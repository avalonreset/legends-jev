"""One explicit HTTPS request, no redirects/retries, sanitized errors only."""
import ctypes
import ctypes.wintypes
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from .core import encoded

API = "https://api.typesafe.ai/v1/"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _windows_dpapi_key():
    if os.name != "nt":
        return None
    local_app = os.environ.get("LOCALAPPDATA")
    if not local_app:
        return None
    dpapi_path = Path(local_app) / "Legends" / "TypeSafe" / "api-key.dpapi"
    if not dpapi_path.is_file():
        return None
    try:
        class DATA_BLOB(ctypes.Structure):
            _fields_ = [("cbData", ctypes.wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

        raw_bytes = bytes.fromhex(dpapi_path.read_text(encoding="utf-8").strip())
        in_buf = ctypes.create_string_buffer(raw_bytes, len(raw_bytes))
        in_blob = DATA_BLOB(len(raw_bytes), in_buf)
        out_blob = DATA_BLOB()
        if not ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
        ):
            return None
        try:
            secret = ctypes.string_at(out_blob.pbData, out_blob.cbData).decode("utf-16-le").strip()
            return secret or None
        finally:
            ctypes.memset(out_blob.pbData, 0, out_blob.cbData)
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)
    except Exception:
        return None


def credential_present():
    return bool(os.environ.get("TYPESAFE_API_KEY") or _windows_dpapi_key())


def uses_images(payload):
    if not isinstance(payload, dict):
        return False
    if payload.get("assets"):
        return True
    questions = payload.get("questions")
    return isinstance(questions, dict) and any(isinstance(q, dict) and q.get("type") == "box" for q in questions.values())


def call(payload=None):
    key = os.environ.get("TYPESAFE_API_KEY") or _windows_dpapi_key()
    if not key:
        raise RuntimeError("credential_not_provisioned")
    data = None if payload is None else encoded(payload)
    headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    if uses_images(payload):
        headers["TypeSafe-Danger-Zone-Images"] = "true"
    req = urllib.request.Request(API + ("models" if data is None else "systemone"), data=data, headers=headers)
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=30) as response:
            body = response.read(1000001)
        if len(body) > 1000000:
            raise RuntimeError("response_too_large")
        return json.loads(body)
    except urllib.error.HTTPError as exc:
        raise RuntimeError("provider_http_" + str(exc.code)) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise RuntimeError("provider_network_or_timeout") from None
    except (ValueError, UnicodeError):
        raise RuntimeError("provider_invalid_json") from None
