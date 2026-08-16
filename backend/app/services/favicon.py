"""favicon 抓取与本地缓存（用户定稿方案：后端缓存，不用 Google 动态获取）。

优先解析首页 HTML 中声明的图标地址；抓取失败做负缓存，避免每次重复请求。
"""
from __future__ import annotations

import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from app.config import settings

CACHE_DIR: Path = settings.data_dir / "favicons"
CACHE_TTL_SECONDS: int = 7 * 24 * 3600  # 成功缓存 7 天后重新抓取
NEGATIVE_TTL_SECONDS: int = 24 * 3600  # 失败负缓存 24 小时内不重试
_TIMEOUT = 5
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

_LINK_TAG_RE = re.compile(r"<link\b[^>]*>", re.IGNORECASE)
_HREF_RE = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
_REL_RE = re.compile(r'rel\s*=\s*["\']([^"\']*)["\']', re.IGNORECASE)


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


def _fail_marker(domain: str) -> Path | None:
    path = CACHE_DIR / f"{_safe_name(domain)}.fail"
    return path if path.exists() else None


def media_type_for(path: Path) -> str:
    return _EXT_TO_MIME.get(path.suffix, "application/octet-stream")


def _detect_mime(data: bytes) -> str | None:
    for magic, mime in _MAGIC_TO_MIME:
        if data.startswith(magic):
            return mime
    if data[:512].lstrip().lower().startswith(b"<svg"):
        return "image/svg+xml"
    return None


def _extract_icon_href(html_text: str) -> str | None:
    """从首页 HTML 中找 <link rel="icon"> 声明的图标地址。"""
    for tag in _LINK_TAG_RE.findall(html_text):
        rel_match = _REL_RE.search(tag)
        if not rel_match:
            continue
        rel = rel_match.group(1).lower()
        tokens = set(rel.split())
        if "icon" not in tokens and "apple-touch-icon" not in rel:
            continue
        href_match = _HREF_RE.search(tag)
        if not href_match:
            continue
        href = href_match.group(1).strip()
        if href and not href.startswith("data:"):
            return href
    return None


def _fetch(url: str) -> tuple[bytes, str] | None:
    """抓取单个 URL，返回 (图片字节, mime)；非图片或失败返回 None。"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = resp.read(_MAX_SIZE)
            header = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
    except Exception:
        return None
    mime = _detect_mime(data)
    if mime is None:
        mime = header if header in MIME_TO_EXT else None
    return (data, mime) if mime else None


def _download(domain: str) -> tuple[bytes, str] | None:
    base = f"https://{domain}"
    candidates: list[str] = []
    try:
        req = urllib.request.Request(base + "/", headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            page = resp.read(_MAX_SIZE).decode("utf-8", errors="ignore")
        icon_href = _extract_icon_href(page)
        if icon_href:
            candidates.append(urllib.parse.urljoin(base + "/", icon_href))
    except Exception:
        pass
    candidates.extend([f"{base}/favicon.ico", f"{base}/favicon.png"])

    seen: set[str] = set()
    for url in candidates:
        if url in seen:
            continue
        seen.add(url)
        result = _fetch(url)
        if result is not None:
            return result
    return None


def fetch_and_cache(domain: str) -> Path | None:
    """确保本地存在该域名的 favicon 缓存（过期则重新抓取），返回文件路径。

    抓取失败时：有旧缓存则兜底返回旧缓存，否则写入失败标记；
    失败标记 24 小时内不再发起网络请求。
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    existing = _existing(domain)
    fail = _fail_marker(domain)
    now = time.time()

    if existing is not None and now - existing.stat().st_mtime < CACHE_TTL_SECONDS:
        return existing
    if fail is not None and now - fail.stat().st_mtime < NEGATIVE_TTL_SECONDS:
        return existing  # 负缓存期内：有旧缓存用旧缓存，没有则 None

    result = _download(domain)
    if result is None:
        marker = CACHE_DIR / f"{_safe_name(domain)}.fail"
        marker.touch()
        return existing

    data, mime = result
    path = CACHE_DIR / f"{_safe_name(domain)}{MIME_TO_EXT[mime]}"
    if existing is not None and existing != path:
        existing.unlink(missing_ok=True)
    path.write_bytes(data)
    if fail is not None:
        fail.unlink(missing_ok=True)
    return path
