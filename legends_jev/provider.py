"""One explicit HTTPS request, no redirects/retries, sanitized errors only."""
import http.client
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request
from .core import encoded, refuse_symlink_tree

API = "https://api.typesafe.ai/v1/"
_API_KEY_RE = re.compile(r"^[\x21-\x7e]{1,512}$")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_api_key_file(path):
    target = refuse_symlink_tree(path, RuntimeError, "api_key_file_symlink_refused")
    if not target.is_file():
        raise RuntimeError("api_key_file_missing")
    try:
        raw = target.read_bytes()
    except OSError:
        raise RuntimeError("api_key_file_unreadable") from None
    if len(raw) > 4096:
        raise RuntimeError("api_key_file_too_large")
    try:
        key = raw.decode("utf-8").strip()
    except UnicodeError:
        raise RuntimeError("api_key_file_invalid") from None
    if not key or not _API_KEY_RE.fullmatch(key):
        raise RuntimeError("api_key_file_invalid")
    return key


def resolve_api_key(api_key_file=None):
    if api_key_file is not None:
        return read_api_key_file(api_key_file)
    raw_env = os.environ.get("TYPESAFE_API_KEY")
    if raw_env is None or not raw_env.strip():
        return None
    key = raw_env.strip()
    if not _API_KEY_RE.fullmatch(key):
        raise RuntimeError("api_key_invalid")
    return key


def credential_present(api_key_file=None):
    try:
        return bool(resolve_api_key(api_key_file))
    except RuntimeError:
        return False


def uses_images(payload):
    if not isinstance(payload, dict):
        return False
    if payload.get("assets"):
        return True
    questions = payload.get("questions")
    return isinstance(questions, dict) and any(isinstance(q, dict) and q.get("type") == "box" for q in questions.values())


def call(payload=None, *, api_key_file=None):
    key = resolve_api_key(api_key_file)
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
    except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError):
        raise RuntimeError("provider_network_or_timeout") from None
    except (ValueError, UnicodeError):
        raise RuntimeError("provider_invalid_json") from None
