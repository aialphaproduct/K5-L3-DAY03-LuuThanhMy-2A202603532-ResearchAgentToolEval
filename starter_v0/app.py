from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
RUNS_DIR = ROOT / "runs"
TRANSCRIPTS_DIR = ROOT / "transcripts"
load_lab_env(ROOT)

st.set_page_config(
    page_title="Research Agent — Tool & Eval Studio",
    page_icon="🔬",
    layout="wide",
)


def init_transcript(provider_name: str, model_name: str | None, version_label: str) -> tuple[Path, dict[str, Any]]:
    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    artifact_ver = build_artifact_version(version_label, system_prompt_path, tools_path)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([
        safe_slug(version_label),
        safe_slug(provider_name),
        timestamp,
    ])
    transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    transcript: dict[str, Any] = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_ver),
        "provider": provider_name,
        "model": model_name,
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "history_window": 5,
        "max_tool_rounds": 4,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    return transcript_path, transcript


with st.sidebar:
    st.title("🔬 Research Agent")
    st.caption("Day 03 Lab v2 — Evidence-Driven Tool Eval")

    provider_name = st.selectbox(
        "Provider",
        options=["openrouter", "openai", "anthropic", "gemini", "ollama"],
        index=0,
    )
    version_label = st.selectbox(
        "Artifact Version Label",
        options=["v0", "v1", "v2", "v3", "v4-local", "v5-local"],
        index=0,
    )
    model_override = st.text_input("Model override (optional)", value="").strip() or None
    max_rounds = st.slider("Max Tool Rounds", min_value=1, max_value=6, value=4)
    history_window = st.slider("History Window (turns)", min_value=1, max_value=10, value=5)

    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    artifact_ver = build_artifact_version(version_label, system_prompt_path, tools_path)

    st.divider()
    st.subheader("📌 Current Artifact Hash")
    st.code(artifact_ver.artifact_version, language="text")
    st.caption(f"Prompt hash: `{artifact_ver.prompt_hash[:12]}`")
    st.caption(f"Tools hash: `{artifact_ver.tools_hash[:12]}`")

    if st.button("🔄 New Chat Session", use_container_width=True):
        for key in ["messages_ui", "history_llm", "transcript_path", "transcript_data", "turn_index"]:
            st.session_state.pop(key, None)
        st.rerun()

    st.divider()
    st.subheader("💡 Câu hỏi mẫu (Click để thử)")
    sample_queries = [
        "Tin tức AI hôm nay có gì nổi bật?",
        "Tweet mới nhất của Sam Altman là gì?",
        "Tóm tắt 5 tweet mới nhất giúp mình",
        "Tóm tắt bài viết này hộ mình",
        "Đăng bản tin AI hôm nay lên Telegram giúp mình",
        "Tìm bài báo khoa học về AI agent evaluation trên arXiv",
        "Chính sách nội bộ của công ty về việc trích dẫn nguồn (source citation) quy định thế nào?",
    ]
    for idx, sample_q in enumerate(sample_queries):
        if st.button(sample_q, key=f"sample_{idx}", use_container_width=True):
            st.session_state["pending_input"] = sample_q


tab_chat, tab_eval, tab_artifacts = st.tabs([
    "💬 Live Agent Chat",
    "📊 Eval Runs & Failure Analysis",
    "🛠️ Tools & Prompt Inspector",
])

with tab_chat:
    st.subheader("💬 Interactive Multi-Round Research Chat")
    st.caption(
        "Hỗ trợ gọi tool nhiều vòng (multi-round), dừng hỏi lại (`clarify`), xác nhận trước khi gửi (`send`), "
        "và tự động lưu log vào `transcripts/*.transcript.json`."
    )

    if "messages_ui" not in st.session_state:
        st.session_state["messages_ui"] = []
    if "history_llm" not in st.session_state:
        st.session_state["history_llm"] = []
    if "turn_index" not in st.session_state:
        st.session_state["turn_index"] = 0
    if "transcript_path" not in st.session_state or "transcript_data" not in st.session_state:
        try:
            prov_obj = make_provider(provider_name)
            default_mod = model_override or getattr(prov_obj, "default_model", None)
        except Exception:
            default_mod = model_override
        t_path, t_data = init_transcript(provider_name, default_mod, version_label)
        st.session_state["transcript_path"] = t_path
        st.session_state["transcript_data"] = t_data

    st.info(f"📝 **Active Transcript File:** `{st.session_state['transcript_path'].name}`")

    for msg in st.session_state["messages_ui"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("tool_events"):
                with st.expander(f"🔧 Tool Calls ({len(msg['tool_events'])}) — Status: `{msg.get('status', '')}`", expanded=False):
                    for idx, ev in enumerate(msg["tool_events"], 1):
                        st.markdown(f"**{idx}. `{ev.get('tool')}`**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.caption("Arguments:")
                            st.json(ev.get("args", {}))
                        with col2:
                            st.caption("Result:")
                            st.json(ev.get("result", {}))

    user_input = st.chat_input("Nhập yêu cầu nghiên cứu của bạn...")
    if "pending_input" in st.session_state:
        user_input = st.session_state.pop("pending_input")

    if user_input:
        st.session_state["messages_ui"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Agent đang suy nghĩ và gọi tool..."):
                system_prompt = system_prompt_path.read_text(encoding="utf-8")
                tool_declarations = load_tool_declarations(tools_path)
                openai_tools = to_openai_tools(tool_declarations)

                st.session_state["turn_index"] += 1
                turn_idx = st.session_state["turn_index"]

                messages = [
                    {"role": "system", "content": system_prompt},
                    *trim_history(st.session_state["history_llm"], history_window),
                    {"role": "user", "content": user_input},
                ]

                turn_record: dict[str, Any] = {
                    "turn_index": turn_idx,
                    "started_at": now_iso(),
                    "user": user_input,
                    "status": "started",
                    "assistant_text": None,
                    "rounds": [],
                    "tool_events": [],
                }

                try:
                    provider = make_provider(provider_name)
                    result = run_model_tool_loop(
                        provider=provider,
                        messages=messages,
                        tools=openai_tools,
                        model=model_override,
                        max_tool_rounds=max_rounds,
                    )
                    turn_record.update(result)
                    assistant_text = result["assistant_text"]
                    status = result["status"]
                    tool_events = result.get("tool_events", [])

                    if tool_events:
                        with st.expander(f"🔧 Tool Calls ({len(tool_events)}) — Status: `{status}`", expanded=True):
                            for idx, ev in enumerate(tool_events, 1):
                                st.markdown(f"**{idx}. `{ev.get('tool')}`**")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.caption("Arguments:")
                                    st.json(ev.get("args", {}))
                                with col2:
                                    st.caption("Result:")
                                    st.json(ev.get("result", {}))

                    st.markdown(assistant_text)

                    st.session_state["history_llm"].append({"role": "user", "content": user_input})
                    st.session_state["history_llm"].append({"role": "assistant", "content": assistant_text})
                    st.session_state["messages_ui"].append({
                        "role": "assistant",
                        "content": assistant_text,
                        "status": status,
                        "tool_events": tool_events,
                    })
                except Exception as exc:
                    err_msg = f"{type(exc).__name__}: {str(exc)}"
                    turn_record.update({"status": "provider_error", "error": err_msg})
                    st.error(f"Lỗi khi gọi provider: {err_msg}")
                    st.session_state["messages_ui"].append({
                        "role": "assistant",
                        "content": f"❌ **ERROR:** `{err_msg}`",
                        "status": "provider_error",
                        "tool_events": [],
                    })

                turn_record["ended_at"] = now_iso()
                st.session_state["transcript_data"]["turns"].append(turn_record)
                write_transcript(st.session_state["transcript_path"], st.session_state["transcript_data"])

with tab_eval:
    st.subheader("📊 Eval Runs & Failure Inspector")
    run_files = sorted(RUNS_DIR.glob("*.json"), reverse=True) if RUNS_DIR.exists() else []

    if not run_files:
        st.warning("Chưa có file kết quả nào trong `runs/*.json`. Hãy chạy `run_eval.py` trước.")
    else:
        selected_run_file = st.selectbox(
            "Chọn Run JSON để phân tích:",
            options=run_files,
            format_func=lambda p: p.name,
        )
        run_data = json.loads(selected_run_file.read_text(encoding="utf-8"))
        summary = run_data.get("summary", {})

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Version", run_data.get("version", "-"))
        c2.metric("Case Accuracy", f"{summary.get('case_accuracy', 0) * 100:.1f}%", f"{summary.get('passed_cases', 0)}/{summary.get('measured_cases', 0)} passed")
        c3.metric("Tool Routing Acc", f"{summary.get('tool_routing_accuracy', 0) * 100:.1f}%")
        c4.metric("Argument Acc", f"{summary.get('argument_accuracy', 0) * 100:.1f}%")
        mt_acc = summary.get("multiturn_accuracy")
        c5.metric("Multi-turn Acc", f"{mt_acc * 100:.1f}%" if mt_acc is not None else "N/A")

        st.caption(
            f"**Artifact Version:** `{run_data.get('artifact_version')}` | "
            f"**Prompt Hash:** `{run_data.get('prompt_hash', '')[:12]}` | "
            f"**Tools Hash:** `{run_data.get('tools_hash', '')[:12]}` | "
            f"**Model:** `{run_data.get('model')}`"
        )

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.markdown("**Failure Counts (by expected failure_type):**")
            st.json(summary.get("failure_counts", {}))
        with col_f2:
            st.markdown("**Observed Mismatch Counts:**")
            st.json(summary.get("observed_mismatch_counts", {}))

        filter_status = st.radio(
            "Lọc kết quả:",
            options=["Tất cả", "Chỉ FAIL", "Chỉ PASS"],
            horizontal=True,
        )

        rows = []
        for item in run_data.get("results", []):
            res = item.get("result", {})
            passed = res.get("passed", False)
            if filter_status == "Chỉ FAIL" and passed:
                continue
            if filter_status == "Chỉ PASS" and not passed:
                continue
            rows.append({
                "Case ID": item.get("id"),
                "Status": "✅ PASS" if passed else "❌ FAIL",
                "Failure Type": res.get("failure_type") or item.get("expect", {}).get("failure_type", ""),
                "Observed Mismatch": res.get("observed_mismatch") or "",
                "Expected Calls": json.dumps(item.get("expect", {}), ensure_ascii=False),
                "Actual Calls": json.dumps(res.get("actual_tool_calls", []), ensure_ascii=False),
                "Failures Detail": "; ".join(res.get("failures", [])),
            })

        st.dataframe(rows, use_container_width=True, hide_index=True)

with tab_artifacts:
    st.subheader("🛠️ Tools & System Prompt Inspector")
    col_a1, col_a2 = st.columns([1, 1])

    with col_a1:
        st.markdown("### 📜 `artifacts/system_prompt.md`")
        st.code(system_prompt_path.read_text(encoding="utf-8"), language="markdown")

        ver_log_path = ARTIFACTS_DIR / "version_log.csv"
        if ver_log_path.exists():
            st.markdown("### 📈 `artifacts/version_log.csv`")
            with ver_log_path.open("r", encoding="utf-8") as f:
                ver_rows = list(csv.DictReader(f))
            st.dataframe(ver_rows, use_container_width=True, hide_index=True)

    with col_a2:
        st.markdown(f"### 🧰 Declared Tools in `artifacts/tools.yaml` ({len(TOOL_FUNCTIONS)} registered in code)")
        declarations = load_tool_declarations(tools_path)
        for t in declarations:
            with st.expander(f"🔧 `{t['name']}` — {t.get('description', '')}", expanded=False):
                st.json(t.get("parameters", {}))

