from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err


API_URL = "https://hn.algolia.com/api/v1/search"
_ALLOWED_TAGS = ("story", "comment", "ask_hn", "show_hn")


def _hit_item(hit: dict[str, Any]) -> dict[str, Any] | None:
    object_id = hit.get("objectID")
    if not object_id:
        return None
    title = hit.get("title") or hit.get("story_title") or "(comment)"
    url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
    summary = hit.get("story_text") or hit.get("comment_text") or ""
    if len(summary) > 400:
        summary = summary[:397] + "..."
    return {
        "title": str(title),
        "url": url,
        "source": "news.ycombinator.com",
        "summary": summary,
        "points": hit.get("points"),
        "type": hit.get("type", "story"),
    }


def hacker_news_search(query: str = "", tag: str = "story", max_results: int = 5) -> dict[str, Any]:
    """Search Hacker News via the public Algolia API (no API key required)."""
    try:
        query = (query or "").strip()
        if not query:
            return {"tool": "hacker_news_search", "query": query, "tag": tag, "items": []}

        params: dict[str, Any] = {
            "query": query,
            "hitsPerPage": max(1, int(max_results or 5)),
        }
        if tag and tag in _ALLOWED_TAGS:
            params["tags"] = tag  # ignore out-of-enum tags instead of failing

        response = requests.get(API_URL, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        items = [item for item in (_hit_item(hit) for hit in data.get("hits", [])) if item]
        return {"tool": "hacker_news_search", "query": query, "tag": tag, "items": items}
    except Exception as exc:
        return err("hacker_news_search", exc)
