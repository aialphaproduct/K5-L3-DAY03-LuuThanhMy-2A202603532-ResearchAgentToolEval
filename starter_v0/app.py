"""Streamlit UI for the Day 03 research agent.

Run:  streamlit run app.py
The agent, tools, prompts and evals are shared with chat.py / run_eval.py.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from chat import now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript  # noqa: E402
from env_loader import load_lab_env  # noqa: E402
from providers import make_provider  # noqa: E402
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools  # noqa: E402
from versioning import artifact_version_dict, build_artifact_version  # noqa: E402

load_lab_env(ROOT)

st.set_page_config(page_title="Research Agent - Day03", page_icon="🔍", layout="wide")

ARTIFACTS_DIR = ROOT / "artifacts"
PROMPT_CHOICES = {
    "v3": ARTIFACTS_DIR / "system_prompt_v3.md",
    "v2": ARTIFACTS_DIR / "system_prompt_v2.md",
    "v1": ARTIFACTS_DIR / "system_prompt_v1.md",
    "v0": ARTIFACTS_DIR / "system_prompt_v0.md",
}

with st.sidebar:
    st.title("⚙️ Cấu hình agent")
    provider_name = st.selectbox(
        "Provider", ["openrouter", "openai", "anthropic", "gemini", "ollama"], index=0
    )
    model = st.text_input("Model (để trống = default của provider)", value="")
    max_tool_rounds = st.slider("Max tool rounds mỗi lượt", 1, 6, 4)
    prompt_choice = st.radio("System prompt", list(PROMPT_CHOICES.keys()))

    st.divider()
    st.caption(f"Tools đã khai báo: {len(TOOL_FUNCTIONS)}")
    with st.expander("Danh sách tool"):
        st.write(", ".join(sorted(TOOL_FUNCTIONS)))
    st.divider()
    if st.button("🗑️ Xoá hội thoại"):
        st.session_state.pop("history", None)
        st.session_state.pop("transcript", None)
        st.session_state.pop("transcript_path", None)
        st.rerun()

prompt_path = PROMPT_CHOICES[prompt_choice]
tools_path = ARTIFACTS_DIR / "tools.yaml"

try:
    system_prompt = prompt_path.read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(tool_declarations)
except Exception as exc:  # noqa: BLE001
    st.error(f"Không đọc được artifacts: {exc}")
    st.stop()


def init_transcript() -> None:
    if "transcript" in st.session_state:
        return
    version = build_artifact_version("ui", prompt_path, tools_path)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = f"ui_{safe_slug(provider_name)}_{timestamp}"
    st.session_state.transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(version),
        "provider": provider_name,
        "model": model or "default",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }


def run_turn(user_text: str) -> None:
    init_transcript()
    history = st.session_state.get("history", [])
    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(history, 5),
        {"role": "user", "content": user_text},
    ]
    turn_record: dict[str, Any] = {
        "turn_index": len(st.session_state.transcript["turns"]) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
    }
    st.session_state.transcript["turns"].append(turn_record)

    try:
        provider = make_provider(provider_name)
        result = run_model_tool_loop(
            provider=provider,
            messages=messages,
            tools=openai_tools,
            model=model or None,
            max_tool_rounds=max_tool_rounds,
        )
        turn_record.update(
            {
                "status": result["status"],
                "assistant_text": result["assistant_text"],
                "rounds": result["rounds"],
                "tool_events": result["tool_events"],
            }
        )
        status_label = {
            "answered": "✅ trả lời",
            "waiting_for_user": "❓ đang chờ bạn bổ sung",
            "max_tool_rounds": "⏳ dừng vì vượt số vòng tool",
        }.get(result["status"], result["status"])
        st.session_state.history.append({"role": "user", "content": user_text})
        st.session_state.history.append(
            {
                "role": "assistant",
                "content": result["assistant_text"] or "(không có nội dung text)",
                "tool_events": result["tool_events"],
                "status": status_label,
            }
        )
    except Exception as exc:  # noqa: BLE001
        turn_record.update(
            {"status": "provider_error", "error": f"{type(exc).__name__}: {str(exc)}"}
        )
        st.session_state.history.append({"role": "user", "content": user_text})
        st.session_state.history.append(
            {
                "role": "assistant",
                "content": f"Lỗi khi gọi provider: `{type(exc).__name__}: {exc}`",
                "tool_events": [],
                "status": "🔥 lỗi",
            }
        )

    turn_record["ended_at"] = now_iso()
    st.session_state.transcript["updated_at"] = now_iso()
    transcript_path = (
        ROOT
        / "transcripts"
        / f"{st.session_state.transcript['transcript_id']}.transcript.json"
    )
    write_transcript(transcript_path, st.session_state.transcript)


# ----------------------------- render history -----------------------------
st.title("🔍 Research Agent — Day 03")
st.caption(
    f"Prompt: {prompt_choice} · Provider: {provider_name} · Model: {model or 'default'}"
)

if "history" not in st.session_state:
    st.session_state.history = []

for message in st.session_state.history:
    avatar = "🙋" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            st.caption(message.get("status", ""))
            tool_events = message.get("tool_events") or []
            if tool_events:
                with st.expander(f"🔧 Tool đã gọi ({len(tool_events)})"):
                    for event in tool_events:
                        st.json(event, expanded=False)

if user_text := st.chat_input(
    "Nhập yêu cầu research… (ví dụ: tin AI hôm nay, tweet của Sam Altman…)"
):
    with st.spinner("Agent đang chạy…"):
        run_turn(user_text)
    st.rerun()

with st.expander("💾 Transcript của phiên này"):
    if "transcript" in st.session_state and st.session_state.transcript["turns"]:
        st.caption(
            f"Lưu tại: {ROOT / 'transcripts' / (st.session_state.transcript['transcript_id'] + '.transcript.json')}"
        )
        st.json(st.session_state.transcript, expanded=False)
    else:
        st.caption("Chưa có lượt nào trong phiên này.")
