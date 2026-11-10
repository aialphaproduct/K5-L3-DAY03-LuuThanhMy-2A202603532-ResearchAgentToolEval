from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, err


def wiki_summary(title: str = "", sentences: int = 3) -> dict[str, Any]:
    """Tra tóm tắt bách khoa (Wikipedia REST, không cần key) cho một khái niệm
    hoặc thực thể có sẵn.

    Dùng cho kiến thức nền ổn định (định nghĩa, 'X là gì'), KHÔNG dùng cho tin
    tức thời sự (đó là `lookup`). Trả về summary + url nguồn. Lỗi mạng / không
    tìm thấy trả về dict lỗi, không raise.
    """
    try:
        name = (title or "").strip()
        if not name:
            raise ValueError("Thiếu title")
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(name.replace(" ", "_"))
        response = requests.get(
            url,
            headers={"User-Agent": os.getenv("ARXIV_USER_AGENT", "Day03-Research-Agent/1.0")},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        extract = (data.get("extract") or "").strip()
        n = max(1, int(sentences or 3))
        pieces = extract.split(". ")
        summary = ". ".join(pieces[:n]).strip()
        if summary and not summary.endswith(".") and len(pieces) > n:
            summary += "."
        page = (data.get("content_urls") or {}).get("desktop", {}).get("page") or ""
        return {
            "tool": "wiki_summary",
            "title": data.get("title") or name,
            "summary": summary,
            "url": page,
            "source": "en.wikipedia.org",
        }
    except Exception as exc:  # noqa: BLE001
        return err("wiki_summary", exc)
