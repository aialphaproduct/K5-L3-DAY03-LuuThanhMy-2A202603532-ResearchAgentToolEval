from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, err


def define_word(word: str = "", lang: str = "en") -> dict[str, Any]:
    """Tra nghĩa của một từ tiếng Anh qua dictionaryapi.dev (không cần key).

    Trả về danh sách nghĩa theo từ loại. Dùng khi người dùng hỏi nghĩa / định
    nghĩa một TỪ cụ thể, không dùng để tra khái niệm dài (đó là `wiki`) hay tin
    tức (`lookup`). Từ không tồn tại / lỗi mạng trả về dict lỗi, không raise.
    """
    try:
        term = (word or "").strip()
        if not term:
            raise ValueError("Thiếu word")
        code = (lang or "en").strip() or "en"
        url = f"https://api.dictionaryapi.dev/api/v2/entries/{code}/" + quote(term)
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        entry = data[0] if isinstance(data, list) and data else {}
        meanings = []
        for meaning in entry.get("meanings", []):
            defs = [d.get("definition") for d in meaning.get("definitions", [])[:2] if d.get("definition")]
            if defs:
                meanings.append({"part_of_speech": meaning.get("partOfSpeech"), "definitions": defs})
        return {
            "tool": "define_word",
            "word": entry.get("word") or term,
            "phonetic": entry.get("phonetic"),
            "meanings": meanings,
            "source": "dictionaryapi.dev",
        }
    except Exception as exc:  # noqa: BLE001
        return err("define_word", exc)
