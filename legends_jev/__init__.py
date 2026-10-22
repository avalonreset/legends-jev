"""Decision advice and optical recognition only; no capture, browser connection, or actuation."""
from .core import (
    MODEL,
    Invalid,
    decide,
    direct,
    inspect_ocr,
    inspect_signage,
    load_image_entry,
    ocr_request,
    pixel_box,
    preflight,
    prepare_image_bytes,
    request,
    signage_request,
    validate,
)
from .provider import call

__version__ = "0.2.0"

__all__ = [
    "MODEL",
    "Invalid",
    "__version__",
    "call",
    "decide",
    "direct",
    "inspect_ocr",
    "inspect_signage",
    "load_image_entry",
    "ocr_request",
    "pixel_box",
    "preflight",
    "prepare_image_bytes",
    "request",
    "signage_request",
    "validate",
]
