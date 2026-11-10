"""Admin dashboard for the Research Agent.

Quản trị & giám sát (chỉ đọc + vài hành động nhẹ):
- 💬 Tin nhắn: hội thoại Telegram và chat UI (từ transcripts/*.transcript.json)
- 🔀 Log luồng chạy: trace từng lượt gọi tool nào, args gì, kết quả ra sao
- 🧪 Log test eval: các lần chạy eval (runs/*.json) + pass/fail từng case

Mở qua thanh điều hướng của Streamlit (app chính = Chat, trang này = Admin).
Deploy public bằng Cloudflare Tunnel: cloudflared tunnel --url http://localhost:8501
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPTS = ROOT / "transcripts"
RUNS = ROOT / "runs"

st.set_page_config(page_title="Admin — Research Agent", page_icon="🗂️", layout="wide")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_json(folder: Path, pattern: str = "*.json") -> list[Path]:
    if not folder.exists():
        return []
    return sorted(folder.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)


def badge(text: str) -> str:
    return f"`{text}`"


def channel_of(t: dict[str, Any]) -> str:
    return t.get("channel") or ("telegram" if "telegram" in t.get("transcript_id", "") else "chat")


# --------------------------------------------------------------------------- #
st.title("🗂️ Admin — Research Agent")
st.caption("Quản trị tin nhắn Telegram, log luồng chạy tool, và log test eval. Chỉ đọc + hành động nhẹ.")

transcripts = list_json(TRANSCRIPTS, "*.transcript.json")
runs = list_json(RUNS, "*.json")

c1, c2, c3 = st.columns(3)
c1.metric("Transcript", len(transcripts))
c2.metric("Lượt hội thoại", sum(len(load_json(p).get("turns", [])) for p in transcripts if load_json(p)))
c3.metric("Run eval", len(runs))

tab_msg, tab_flow, tab_eval = st.tabs(["💬 Tin nhắn", "🔀 Log luồng chạy", "🧪 Log test eval"])


# =========================== TAB 1: Tin nhắn =============================== #
with tab_msg:
    if not transcripts:
        st.info("Chưa có transcript nào. Chat qua app chính hoặc bot Telegram để sinh dữ liệu.")
    else:
        channels = sorted({channel_of(load_json(p) or {}) for p in transcripts})
        pick_ch = st.multiselect("Lọc theo kênh", channels, default=channels)
        options = []
        for p in transcripts:
            t = load_json(p) or {}
            if channel_of(t) in pick_ch:
                options.append((f"[{channel_of(t)}] {p.name} · {len(t.get('turns', []))} lượt · {t.get('model','')}", p))
        if not options:
            st.warning("Không có transcript khớp bộ lọc.")
        else:
            label = st.selectbox("Chọn hội thoại", [o[0] for o in options])
            path = dict(options)[label]
            t = load_json(path) or {}
            st.caption(
                f"{badge(channel_of(t))} · model {badge(t.get('model',''))} · "
                f"version {badge(t.get('artifact_version',''))} · tạo {t.get('created_at','')}"
            )
            for turn in t.get("turns", []):
                with st.chat_message("user"):
                    st.markdown(turn.get("user", ""))
                with st.chat_message("assistant"):
                    rounds = turn.get("rounds", [])
                    tools_used = [tc["name"] for rnd in rounds for tc in rnd.get("tool_calls", [])]
                    if tools_used:
                        st.caption("🔧 tool: " + ", ".join(f"`{x}`" for x in tools_used))
                    st.markdown(turn.get("assistant_text") or "_(không có nội dung)_")
                    status = turn.get("status")
                    if status and status not in {"answered", "waiting_for_user"}:
                        st.warning(f"status: {status}" + (f" — {turn.get('error','')}" if turn.get("error") else ""))
            with st.expander("⬇️ JSON transcript gốc"):
                st.json(t)


# ====================== TAB 2: Log luồng chạy (trace) ====================== #
with tab_flow:
    st.caption("Mỗi dòng là một lượt: người dùng hỏi gì → agent gọi tool nào (args) → kết quả. Dùng để 'test luồng chạy'.")
    rows: list[dict[str, Any]] = []
    for p in transcripts:
        t = load_json(p) or {}
        ch = channel_of(t)
        for turn in t.get("turns", []):
            calls = [f"{tc['name']}({json.dumps(tc.get('args', {}), ensure_ascii=False)})"
                     for rnd in turn.get("rounds", []) for tc in rnd.get("tool_calls", [])]
            rows.append({
                "time": turn.get("started_at", ""),
                "kênh": ch,
                "user": (turn.get("user", "") or "")[:80],
                "tool_calls": " | ".join(calls) if calls else "(trả lời trực tiếp)",
                "status": turn.get("status", ""),
            })
    if not rows:
        st.info("Chưa có log luồng chạy.")
    else:
        rows.sort(key=lambda r: r["time"], reverse=True)
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.divider()
        st.subheader("Xem chi tiết một lượt (full trace: args + result)")
        idx = st.number_input("Chỉ số dòng (0 = mới nhất)", min_value=0, max_value=max(0, len(rows) - 1), value=0)
        # Rebuild the matching turn to show full tool results.
        flat = []
        for p in transcripts:
            t = load_json(p) or {}
            for turn in t.get("turns", []):
                flat.append((turn.get("started_at", ""), turn))
        flat.sort(key=lambda x: x[0], reverse=True)
        if flat:
            _, turn = flat[int(idx)]
            st.markdown(f"**User:** {turn.get('user','')}")
            for rnd in turn.get("rounds", []):
                st.markdown(f"**Vòng {rnd.get('round','?')}**")
                for ev in rnd.get("tool_results", []):
                    st.markdown(f"🔧 `{ev.get('tool')}`")
                    cc1, cc2 = st.columns(2)
                    cc1.caption("args"); cc1.code(json.dumps(ev.get("args", {}), ensure_ascii=False, indent=2), language="json")
                    cc2.caption("result"); cc2.code(json.dumps(ev.get("result", {}), ensure_ascii=False, indent=2)[:4000], language="json")
            st.markdown(f"**Agent:** {turn.get('assistant_text','')}")


# =========================== TAB 3: Log test eval ========================== #
with tab_eval:
    if not runs:
        st.info("Chưa có run eval nào trong runs/.")
    else:
        summary_rows = []
        for p in runs:
            d = load_json(p) or {}
            s = d.get("summary", {})
            summary_rows.append({
                "run": p.name,
                "version": d.get("version", ""),
                "suite": d.get("suite", ""),
                "model": d.get("model", ""),
                "case_acc": s.get("case_accuracy"),
                "routing": s.get("tool_routing_accuracy"),
                "arg": s.get("argument_accuracy"),
                "multiturn": s.get("multiturn_accuracy"),
                "passed": f"{s.get('passed_cases','?')}/{s.get('total_cases','?')}",
            })
        st.subheader("Tổng hợp các run")
        st.dataframe(summary_rows, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Chi tiết một run (pass/fail từng case)")
        pick = st.selectbox("Chọn run", [p.name for p in runs])
        d = load_json(RUNS / pick) or {}
        s = d.get("summary", {})
        st.caption(
            f"version {badge(d.get('version',''))} · suite {badge(d.get('suite',''))} · "
            f"model {badge(d.get('model',''))} · acc {badge(str(s.get('case_accuracy')))}"
        )
        case_rows = []
        for r in d.get("results", []):
            res = r.get("result", {})
            calls = [c.get("name") for c in (res.get("actual_tool_calls") or [])]
            case_rows.append({
                "case": r.get("id"),
                "pass": "✅" if res.get("passed") else "❌",
                "tools": ", ".join(calls) if calls else "(no tool)",
                "failure_type": res.get("failure_type") or "",
                "failures": " ; ".join(res.get("failures") or []),
            })
        st.dataframe(case_rows, use_container_width=True, hide_index=True)
        with st.expander("⬇️ JSON run gốc"):
            st.json(d)


# --------------------------- Hành động nhẹ --------------------------------- #
with st.sidebar:
    st.header("Gửi nhanh qua Telegram")
    st.caption("Dùng TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID trong .env.")
    msg = st.text_area("Nội dung", "")
    ok = st.checkbox("Tôi xác nhận gửi")
    if st.button("Gửi", disabled=not (msg.strip() and ok)):
        try:
            from env_loader import load_lab_env
            load_lab_env(ROOT)
            from tools.send.tool import send_telegram
            res = send_telegram(text=msg, confirmed=True)
            if res.get("status") == "sent":
                st.success("Đã gửi ✅")
            else:
                st.error(f"Không gửi được: {res}")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Lỗi: {exc}")
