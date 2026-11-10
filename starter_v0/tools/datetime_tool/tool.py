from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from tools._shared import err


def current_datetime(timezone: str = "UTC", fmt: str = "iso") -> dict[str, Any]:
    """Trả về ngày giờ hiện tại theo một múi giờ IANA (ví dụ 'UTC',
    'Asia/Ho_Chi_Minh', 'America/New_York').

    `fmt="iso"` trả chuỗi ISO 8601; mọi giá trị khác được coi là chuỗi
    định dạng strftime (ví dụ '%Y-%m-%d %H:%M'). Múi giờ sai trả về dict lỗi.
    """
    try:
        tz_name = (timezone or "UTC").strip() or "UTC"
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)
        formatted = now.isoformat() if (fmt or "iso") == "iso" else now.strftime(fmt)
        return {
            "tool": "current_datetime",
            "timezone": tz_name,
            "datetime": formatted,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "weekday": now.strftime("%A"),
        }
    except Exception as exc:  # noqa: BLE001
        return err("current_datetime", exc)
