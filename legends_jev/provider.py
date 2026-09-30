"""One explicit HTTPS request, no redirects/retries, sanitized errors only."""
import json
import os
import urllib.error
import urllib.request
from .core import encoded

API = "https://api.typesafe.ai/v1/"

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def call(payload=None):
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise RuntimeError("credential_not_provisioned")
    data = None if payload is None else encoded(payload)
    req = urllib.request.Request(API + ("models" if data is None else "systemone"), data=data,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
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
