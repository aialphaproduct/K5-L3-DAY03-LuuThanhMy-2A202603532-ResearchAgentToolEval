from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err


API_URL = "https://api.github.com/search/repositories"
_ALLOWED_SORTS = ("stars", "forks", "updated", "best_match")


def _repo_item(repo: dict[str, Any]) -> dict[str, Any] | None:
    full_name = repo.get("full_name")
    if not full_name:
        return None
    return {
        "title": full_name,
        "url": repo.get("html_url") or f"https://github.com/{full_name}",
        "source": "github.com",
        "summary": (repo.get("description") or "")[:400],
        "stars": repo.get("stargazers_count"),
        "language": repo.get("language"),
    }


def repo_search(query: str = "", sort: str = "stars", max_results: int = 5) -> dict[str, Any]:
    """Search public GitHub repositories (GitHub Search API, no key needed for light use)."""
    try:
        sort = (sort or "stars").strip().lower() or "stars"
        if sort not in _ALLOWED_SORTS:
            raise ValueError(f"Unsupported sort: {sort!r} (allowed: stars, forks, updated)")
        query = (query or "").strip()
        if not query:
            return {"tool": "repo_search", "query": query, "sort": sort, "items": []}

        response = requests.get(
            API_URL,
            params={"q": query, "sort": sort, "per_page": max(1, int(max_results or 5))},
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "AI20k-Day03-Research-Agent/1.0 (educational lab)",
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        items = [item for item in (_repo_item(repo) for repo in data.get("items", [])) if item]
        return {"tool": "repo_search", "query": query, "sort": sort, "total_count": data.get("total_count", 0), "items": items}
    except Exception as exc:
        return err("repo_search", exc)
