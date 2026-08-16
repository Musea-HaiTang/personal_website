"""favicon 抓取与本地缓存（用户定稿方案：后端缓存，不用 Google 动态获取）。"""
from __future__ import annotations

import re
import time
import urllib.request
from pathlib import Path

from app.config import settings

CACHE_DIR: Path = settings.data_dir / "favicons"
CACHE_TTL_SECONDS: int = 7 * 24 * 3600  # 缓存 7 天后重新抓取
_MAX_SIZE = 512 * 1024
_USER_AGENT = "personal-website-favicon/0.1"

DOMAIN_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*$")

_MAGIC_TO_MIME = (
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\x00\x00\x01\x00", "image/x-icon"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"RIFF", "image/webp"),
)
MIME_TO_EXT = {
    "image/png": ".png",
    "image/x-icon": ".ico",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}
_EXT_TO_MIME = {ext: mime for mime, ext in MIME_TO_EXT.items()}


def sanitize_domain(domain: str) -> str | None:
    """校验并规范化域名，非法时返回 None。"""
    d = (domain or "").strip().lower()
    if not DOMAIN_RE.fullmatch(d) or len(d) > 255:
        return None
    return d


def _safe_name(domain: str) -> str:
    return re.sub(r"[^a-z0-9.-]", "_", domain)


def _existing(domain: str) -> Path | None:
    for ext in MIME_TO_EXT.values():
        path = CACHE_DIR / f"{_safe_name(domain)}{ext}"
        if path.exists():
            return path
    return None


def media_type_for(path: Path) -> str:
    return _EXT_TO_MIME.get(path.suffix, "application/octet-stream")


def _detect_mime(data: bytes) -> str | None:
    for magic, mime in _MAGIC_TO_MIME:
        if data.startswith(magic):
            return mime
    if data[:512].lstrip().lower().startswith(b"<svg"):
        return "image/svg+xml"
    return None


def _download(domain: str) -> tuple[bytes, str] | None:
    candidates = [f"https://{domain}/favicon.ico", f"https://{domain}/favicon.png"]
    for url in candidates:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = resp.read(_MAX_SIZE)
                header = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
            mime = _detect_mime(data)
            if mime is None:
                mime = header if header in MIME_TO_EXT else None
            if mime:
                return data, mime
        except Exception:
            continue
    return None


def fetch_and_cache(domain: str) -> Path | None:
    """确保本地存在该域名的 favicon 缓存（过期则重新抓取），返回文件路径。

    抓取失败时保留旧缓存兜底；既无缓存也抓取失败时返回 None。
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    existing = _existing(domain)
    if existing is not None and time.time() - existing.stat().st_mtime < CACHE_TTL_SECONDS:
        return existing

    result = _download(domain)
    if result is None:
        return existing

    data, mime = result
    path = CACHE_DIR / f"{_safe_name(domain)}{MIME_TO_EXT[mime]}"
    if existing is not None and existing != path:
        existing.unlink(missing_ok=True)
    path.write_bytes(data)
    return path
