"""Streamlit UI for the Day 03 Research Agent.

Reuses the exact tool-calling loop logic from chat.py (same transcript format),
but renders each tool round in the browser instead of the terminal.

Run:
    streamlit run app.py
Then pick a provider/version in the sidebar and chat.

Transcripts are written to transcripts/*.transcript.json, identical in shape
to the ones chat.py produces, so they are valid submission evidence.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

# Reuse helpers from chat.py so the agent behaviour and transcript format
# stay identical between the CLI (chat.py) and this UI.
from chat import (
    assistant_tool_message,
    execute_tool_call,
    json_text,
    now_iso,
    safe_slug,
    tool_results_message,
    trim_history,
    write_transcript,
)

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

PROVIDERS = ["openrouter", "openai", "anthropic", "gemini", "ollama"]


# --------------------------------------------------------------------------- #
# Agent loop (Streamlit-aware version of chat.run_model_tool_loop)
# --------------------------------------------------------------------------- #
def run_tool_loop(
    *,
    provider: Any,
    messages: list[dict[str, str]],
    tools: list[dict[str, Any]],
    model: str | None,
    max_tool_rounds: int,
    render,
) -> dict[str, Any]:
    """Drive the model -> tool -> model loop, calling render(round_record)
    after each round so the UI can show tool calls live."""
    working_messages = list(messages)
    rounds: list[dict[str, Any]] = []
    all_tool_events: list[dict[str, Any]] = []

    for round_index in range(1, max_tool_rounds + 1):
        response = provider.complete(working_messages, tools, model=model, temperature=0.0)
        calls = response.tool_calls
        round_record: dict[str, Any] = {
            "round": round_index,
            "assistant_text": response.text,
            "tool_calls": [{"name": c.name, "args": c.args} for c in calls],
            "tool_results": [],
        }

        if not calls:
            render(round_record)
            rounds.append(round_record)
            return {
                "status": "answered",
                "assistant_text": response.text or "",
                "rounds": rounds,
                "tool_events": all_tool_events,
            }

        working_messages.append(assistant_tool_message(response.text, calls))
        non_clarification_events: list[dict[str, Any]] = []

        for call in calls:
            event = execute_tool_call(call)
            round_record["tool_results"].append(event)
            all_tool_events.append(event)

            result = event.get("result", {})
            if isinstance(result, dict) and result.get("awaiting_user"):
                question = (
                    result.get("question")
                    or call.args.get("question")
                    or "Bạn bổ sung thêm thông tin nhé."
                )
                render(round_record)
                rounds.append(round_record)
                return {
                    "status": "waiting_for_user",
                    "assistant_text": question,
                    "rounds": rounds,
                    "tool_events": all_tool_events,
                }

            non_clarification_events.append(event)

        render(round_record)
        rounds.append(round_record)
        working_messages.append(tool_results_message(non_clarification_events))

    return {
        "status": "max_tool_rounds",
        "assistant_text": f"Dừng sau {max_tool_rounds} vòng tool. Xem transcript để biết chi tiết.",
        "rounds": rounds,
        "tool_events": all_tool_events,
    }


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def render_round(round_record: dict[str, Any]) -> None:
    """Render one tool round inside the current chat message."""
    text = round_record.get("assistant_text")
    if text and round_record.get("tool_calls"):
        st.markdown(text)
    for call, result_event in zip(
        round_record.get("tool_calls", []),
        round_record.get("tool_results", []) + [None] * len(round_record.get("tool_calls", [])),
    ):
        label = f"🔧 `{call['name']}`"
        with st.expander(label, expanded=False):
            st.caption("arguments")
            st.code(json_text(call.get("args", {})), language="json")
            if result_event is not None:
                st.caption("result")
                st.code(json_text(result_event.get("result", {}), max_chars=6000), language="json")


def render_history() -> None:
    for item in st.session_state.display:
        with st.chat_message(item["role"]):
            if item["role"] == "assistant":
                for rr in item.get("rounds", []):
                    render_round(rr)
            st.markdown(item["content"])


# --------------------------------------------------------------------------- #
# Session setup
# --------------------------------------------------------------------------- #
def init_session(cfg: dict[str, Any]) -> None:
    """(Re)start a chat session with the given config: fresh history + transcript."""
    system_prompt = Path(cfg["system_prompt"]).read_text(encoding="utf-8")
    declarations = load_tool_declarations(Path(cfg["tools"]))
    openai_tools = to_openai_tools(declarations)
    provider = make_provider(cfg["provider"])
    selected_model = cfg["model"] or getattr(provider, "default_model", None)
    artifact_version = build_artifact_version(
        cfg["version"], Path(cfg["system_prompt"]), Path(cfg["tools"])
    )

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(cfg["version"]), safe_slug(cfg["provider"]), timestamp])
    transcript_path = ROOT / "transcripts" / f"{transcript_id}.transcript.json"
    transcript: dict[str, Any] = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": cfg["provider"],
        "model": selected_model,
        "system_prompt": str(cfg["system_prompt"]),
        "tools": str(cfg["tools"]),
        "history_window": cfg["history_window"],
        "max_tool_rounds": cfg["max_tool_rounds"],
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
        "ui": "streamlit",
    }

    st.session_state.cfg = cfg
    st.session_state.system_prompt = system_prompt
    st.session_state.openai_tools = openai_tools
    st.session_state.provider = provider
    st.session_state.selected_model = selected_model
    st.session_state.artifact_version = artifact_version
    st.session_state.transcript = transcript
    st.session_state.transcript_path = transcript_path
    st.session_state.history = []        # model context (user/assistant pairs)
    st.session_state.display = []        # what we render
    st.session_state.turn_index = 0
    st.session_state.started = True


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="Research Agent — Day 03", page_icon="🔎", layout="centered")
st.title("🔎 Research Agent")

with st.sidebar:
    st.header("Cấu hình")
    provider = st.selectbox("Provider", PROVIDERS, index=0)
    model = st.text_input("Model (để trống = mặc định của provider)", value="").strip() or None
    version = st.text_input("Version label", value="v0")
    system_prompt_path = st.text_input("System prompt", value=str(ARTIFACTS_DIR / "system_prompt.md"))
    tools_path = st.text_input("Tools YAML", value=str(ARTIFACTS_DIR / "tools.yaml"))
    history_window = st.number_input("History window (số cặp lượt giữ lại)", 0, 50, 5)
    max_tool_rounds = st.number_input("Max tool rounds", 1, 12, 4)

    start = st.button("🚀 Bắt đầu / Reset phiên", type="primary", use_container_width=True)
    if start:
        init_session(
            {
                "provider": provider,
                "model": model,
                "version": version,
                "system_prompt": system_prompt_path,
                "tools": tools_path,
                "history_window": int(history_window),
                "max_tool_rounds": int(max_tool_rounds),
            }
        )

    if st.session_state.get("started"):
        av = st.session_state.artifact_version
        st.success("Phiên đang chạy")
        st.caption(f"artifact_version: `{av.artifact_version}`")
        st.caption(f"model: `{st.session_state.selected_model}`")
        st.caption(f"transcript: `{st.session_state.transcript_path.name}`")

if not st.session_state.get("started"):
    st.info("Chọn provider + version ở thanh bên rồi bấm **Bắt đầu / Reset phiên** để chat.")
    st.stop()

# Render prior turns
render_history()

# Chat input
user_text = st.chat_input("Nhập yêu cầu nghiên cứu của bạn…")
if user_text:
    cfg = st.session_state.cfg
    st.session_state.turn_index += 1

    with st.chat_message("user"):
        st.markdown(user_text)
    st.session_state.display.append({"role": "user", "content": user_text, "rounds": []})

    messages = [
        {"role": "system", "content": st.session_state.system_prompt},
        *trim_history(st.session_state.history, cfg["history_window"]),
        {"role": "user", "content": user_text},
    ]

    turn_record: dict[str, Any] = {
        "turn_index": st.session_state.turn_index,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    with st.chat_message("assistant"):
        rendered_rounds: list[dict[str, Any]] = []

        def _render(rr: dict[str, Any]) -> None:
            render_round(rr)
            rendered_rounds.append(rr)

        try:
            with st.spinner("Agent đang suy nghĩ & gọi tool…"):
                result = run_tool_loop(
                    provider=st.session_state.provider,
                    messages=messages,
                    tools=st.session_state.openai_tools,
                    model=st.session_state.selected_model,
                    max_tool_rounds=cfg["max_tool_rounds"],
                    render=_render,
                )
            turn_record.update(result)
            assistant_text = result["assistant_text"]
            if result["status"] == "waiting_for_user":
                st.info("⏳ Agent cần bạn bổ sung thông tin:")
            st.markdown(assistant_text)

            st.session_state.history.append({"role": "user", "content": user_text})
            st.session_state.history.append({"role": "assistant", "content": assistant_text})
            st.session_state.display.append(
                {"role": "assistant", "content": assistant_text, "rounds": rendered_rounds}
            )
        except Exception as exc:  # noqa: BLE001 — surface provider/network errors in UI
            error = f"{type(exc).__name__}: {exc}"
            turn_record.update({"status": "provider_error", "error": error})
            st.error(f"Lỗi: {error}")
            st.session_state.display.append(
                {"role": "assistant", "content": f"⚠️ {error}", "rounds": rendered_rounds}
            )

    turn_record["ended_at"] = now_iso()
    st.session_state.transcript["turns"].append(turn_record)
    write_transcript(st.session_state.transcript_path, st.session_state.transcript)
