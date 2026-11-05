"""Offline release checks for links, private residue, EDR hygiene, version parity, and required artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", "dist", "build", "__pycache__", ".pytest_cache", ".integration", "var"}
REQUIRED = [
    "README.md",
    "LICENSE",
    "NOTICE",
    "THIRD_PARTY_NOTICES.md",
    "AGENTS.md",
    "SECURITY.md",
    "SUPPORT.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "CHANGELOG.md",
    "docs/AGENT-RECIPE.md",
    "docs/BENCHMARK.md",
    "docs/SEARCH-STRATEGY.md",
    "docs/UPSTREAM.md",
    "legends_jev/docs/recipe.md",
    "skills/cto-legends/SKILL.md",
    ".legends-module",
    "assets/manifest.json",
]
TEXT_SUFFIXES = {".md", ".py", ".json", ".toml", ".yml", ".in", ".txt", ".cfg", ".ini", ".cff"}
FORBIDDEN = [
    r"(?i)[a-z]:\\+users\\+",
    r"(?i)\.tail[a-z0-9]+\.ts\.net",
    r"(?i)sk_live_[a-z0-9]{12,}",
    r"(?i)rk_live_[a-z0-9]{12,}",
    r"gh[pousr]_[A-Za-z0-9]{20,}",
    r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----",
    r"CREATE_NO_WINDOW",
    r"0x08000000",
    r"(?i)-WindowStyle\s+Hidden",
    r"(?i)-ExecutionPolicy\s+Bypass",
    r"ctypes\.windll",
    r"(?i)CryptUnprotectData",
    r"(?i)GetAsyncKeyState",
    r"(?i)IndexedDB",
    r"(?i)api-key\.dpapi",
    r"(?i)Invoke-Jev\.ps1",
    r"(?i)legends-shell-kit",
    r"(?i)legends-chrome-kit",
]
FORBIDDEN_FILES = {".pem", ".key", ".p12", ".pfx", ".ps1", ".bat", ".cmd", ".vbs", ".ahk"}
PNG_METADATA_CHUNKS = {"tEXt", "iTXt", "zTXt", "eXIf"}
WEBP_METADATA_CHUNKS = {b"EXIF", b"XMP "}


def image_metadata_issues(path: Path) -> list[str]:
    """Flag raster metadata chunks that can carry authoring residue."""
    try:
        raw = path.read_bytes()
    except OSError:
        return [f"Cannot read image: {path}"]
    issues: list[str] = []
    suffix = path.suffix.lower()
    if suffix == ".png":
        if raw[:8] != b"\x89PNG\r\n\x1a\n":
            return [f"Not a PNG file: {path}"]
        offset = 8
        while offset + 8 <= len(raw):
            length = struct.unpack(">I", raw[offset : offset + 4])[0]
            chunk = raw[offset + 4 : offset + 8]
            try:
                name = chunk.decode("latin1")
            except UnicodeError:
                break
            if name in PNG_METADATA_CHUNKS:
                issues.append(f"Image metadata chunk {name} in {path.name}; strip authoring residue.")
            if name == "IEND":
                break
            offset += 12 + length
    elif suffix == ".webp":
        if raw[:4] != b"RIFF" or raw[8:12] != b"WEBP":
            return [f"Not a WebP file: {path}"]
        offset = 12
        while offset + 8 <= len(raw):
            tag = raw[offset : offset + 4]
            length = struct.unpack("<I", raw[offset + 4 : offset + 8])[0]
            if tag in WEBP_METADATA_CHUNKS:
                issues.append(f"Image metadata chunk {tag!r} in {path.name}; strip authoring residue.")
                break
            offset += 8 + length + (length % 2)
    return issues


def _check_version_parity(root: Path, errors: list[str]) -> None:
    if (root / "VERSION").exists():
        errors.append("Duplicate VERSION file present; pyproject.toml must be the sole version file.")
    pyproject = root / "pyproject.toml"
    init_py = root / "legends_jev" / "__init__.py"
    changelog = root / "CHANGELOG.md"
    if not (pyproject.is_file() and init_py.is_file() and changelog.is_file()):
        return
    m_py = re.search(r'^version\s*=\s*"(\d+\.\d+\.\d+)"', pyproject.read_text(encoding="utf-8-sig"), re.M)
    m_init = re.search(r'^__version__\s*=\s*"(\d+\.\d+\.\d+)"', init_py.read_text(encoding="utf-8-sig"), re.M)
    m_cl = re.search(r"^##\s+\[?v?(\d+\.\d+\.\d+)\b", changelog.read_text(encoding="utf-8-sig"), re.M)
    v_py = m_py.group(1) if m_py else None
    v_init = m_init.group(1) if m_init else None
    v_cl = m_cl.group(1) if m_cl else None
    if len({v_py, v_init, v_cl}) != 1 or v_py is None:
        errors.append(
            f"Version parity mismatch: pyproject={v_py}, __init__={v_init}, CHANGELOG={v_cl}"
        )


def check(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for name in REQUIRED:
        if not (root / name).is_file():
            errors.append(f"Missing required file: {name}")

    _check_version_parity(root, errors)

    manifest = root / "assets" / "manifest.json"
    if manifest.is_file():
        try:
            entries = json.loads(manifest.read_text(encoding="utf-8-sig"))["files"]
        except (ValueError, KeyError):
            errors.append("assets/manifest.json is not a manifest with files.")
            entries = []
        for entry in entries:
            target = root / "assets" / entry.get("name", "")
            try:
                raw = target.read_bytes()
            except OSError:
                errors.append(f"Manifest asset missing: {entry.get('name')}")
                continue
            if len(raw) != entry.get("bytes"):
                errors.append(f"Manifest byte mismatch: {entry.get('name')}")
            if hashlib.sha256(raw).hexdigest() != entry.get("sha256"):
                errors.append(f"Manifest hash mismatch: {entry.get('name')}")

    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if not path.is_file() or any(p in SKIP or p.endswith(".egg-info") for p in rel.parts):
            continue
        if path.suffix.lower() in FORBIDDEN_FILES:
            errors.append(f"Forbidden file extension must not ship: {rel}")
            continue
        if path.suffix.lower() in {".png", ".webp"}:
            errors.extend(f"{rel}: {issue}" for issue in image_metadata_issues(path))
            continue
        if path.suffix not in TEXT_SUFFIXES and path.name not in {"LICENSE", "NOTICE"}:
            continue
        text = path.read_text(encoding="utf-8-sig")
        if path.name not in {"check_release.py", "check_wheel.py"}:
            for pattern in FORBIDDEN:
                if re.search(pattern, text):
                    errors.append(f"Possible private or EDR-sensitive residue ({pattern}): {rel}")
        if path.suffix != ".md":
            continue
        if "\u2014" in text or "\u2013" in text:
            errors.append(f"Disallowed dash in copy: {rel}")
        for target_link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            if target_link.startswith(("https://", "http://", "mailto:", "#")):
                continue
            cleaned = unquote(target_link.split("#", 1)[0].split("?", 1)[0])
            resolved = (path.parent / cleaned).resolve()
            if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                errors.append(f"Broken or external local link: {rel}: {target_link}")
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Offline release checks.")
    parser.add_argument("--root", type=Path, default=ROOT)
    options = parser.parse_args()
    failures = check(options.root)
    for failure in failures:
        print(failure)
    print(f"Release checks: {'FAIL' if failures else 'PASS'} ({len(failures)} issues)")
    sys.exit(bool(failures))
