from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, err


_ALLOWED_LANGUAGES = ("en", "vi")
_TAG_RE = re.compile(r"<[^>]+>")


def _clean_snippet(snippet: str) -> str:
    text = _TAG_RE.sub("", snippet)
    text = text.replace("&quot;", '"').replace("&amp;", "&")
    return re.sub(r"\s+", " ", text).strip()


def wiki_lookup(query: str = "", language: str = "en", max_results: int = 5) -> dict[str, Any]:
    """Search Wikipedia article titles and snippets (MediaWiki API, no key)."""
    try:
        language = (language or "en").strip().lower()
        if language not in _ALLOWED_LANGUAGES:
            raise ValueError(f"Unsupported Wikipedia language: {language!r} (allowed: en, vi)")
        query = (query or "").strip()
        if not query:
            return {"tool": "wiki_lookup", "query": query, "language": language, "items": []}

        response = requests.get(
            f"https://{language}.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": max(1, int(max_results or 5)),
                "format": "json",
            },
            headers={"User-Agent": "AI20k-Day03-Research-Agent/1.0 (educational lab)"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        results = response.json().get("query", {}).get("search", [])
        items = [{
            "title": result.get("title"),
            "url": f"https://{language}.wikipedia.org/wiki/{quote(str(result.get('title') or '').replace(' ', '_'))}",
            "source": f"{language}.wikipedia.org",
            "summary": _clean_snippet(result.get("snippet") or ""),
        } for result in results if result.get("title")]
        return {"tool": "wiki_lookup", "query": query, "language": language, "items": items}
    except Exception as exc:
        return err("wiki_lookup", exc)
