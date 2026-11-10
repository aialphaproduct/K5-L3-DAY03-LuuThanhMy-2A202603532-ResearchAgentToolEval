from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from tools._shared import ROOT, err


NOTES_PATH = ROOT / "notes" / "notes.json"
_MAX_NOTES = 200
_ALLOWED_ACTIONS = ("save", "list")


def _slugify_title(text: str, max_chars: int = 60) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    folded = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    slug = re.sub(r"[^a-z0-9]+", "_", folded).strip("_")
    return slug[:max_chars] or "note"


def _read_notes(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []  # tolerate a corrupt note file; the tool never crashes the agent


def notes(action: str = "list", text: str = "", title: str = "", limit: int = 10) -> dict[str, Any]:
    """Local scratchpad: `save` appends a note to notes/notes.json, `list` reads them back."""
    try:
        action = (action or "").strip().lower()
        if action not in _ALLOWED_ACTIONS:
            raise ValueError(f"Unsupported action: {action!r} (allowed: save, list)")

        if action == "save":
            note_text = (text or "").strip()
            if not note_text:
                raise ValueError("text is empty; a note should have content")
            NOTES_PATH.parent.mkdir(parents=True, exist_ok=True)
            existing = _read_notes(NOTES_PATH)
            entry = {
                "id": len(existing) + 1,
                "title": (title or "").strip() or _slugify_title(note_text),
                "text": note_text,
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
            existing.append(entry)
            NOTES_PATH.write_text(json.dumps(existing[-_MAX_NOTES:], ensure_ascii=False, indent=2), encoding="utf-8")
            return {"tool": "notes", "action": "save", "saved": entry, "note_count": len(existing)}

        # action == "list"
        existing = _read_notes(NOTES_PATH)
        try:
            limit_int = int(limit or 10)
        except (TypeError, ValueError):
            limit_int = 10
        limit_int = max(1, limit_int)
        return {
            "tool": "notes",
            "action": "list",
            "items": existing[-limit_int:],
            "note_count": len(existing),
        }
    except Exception as exc:
        return err("notes", exc)
