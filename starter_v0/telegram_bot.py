"""Two-way Telegram bridge for the Day 03 Research Agent.

You message the bot in Telegram -> this script runs the SAME agent loop as
chat.py -> the bot replies to you in Telegram.

Run (after .env has TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID):
    python telegram_bot.py --provider openrouter --version v3

Stop with Ctrl+C.

Notes
-----
* Uses Telegram long-polling (getUpdates). No public URL / webhook needed.
* By default it only answers the chat in TELEGRAM_CHAT_ID (so random people
  can't burn your model credits). Pass --open to answer anyone.
* Old messages sent before the bot started are skipped unless --backlog.
* Every turn is logged to transcripts/*.transcript.json (same format as chat.py).
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# Windows consoles default to cp1252 and crash on emoji / Vietnamese prints.
# Force UTF-8 so the agent loop (which prints 🔧 tool calls) never dies on output.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

# Reuse the exact agent loop + helpers from the CLI chat.
from chat import now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

START_MESSAGE = (
    "👋 Xin chào! Mình là Research Agent (Day 03).\n"
    "Gửi cho mình một yêu cầu nghiên cứu, ví dụ:\n"
    "• Tổng hợp tin mới nhất về OpenAI\n"
    "• Tóm tắt các bài đăng gần đây của @elonmusk\n"
    "• Tìm paper arXiv về LLM agent\n\n"
    "Gõ /reset để xoá lịch sử hội thoại."
)


def tg_api(token: str, method: str) -> str:
    return f"https://api.telegram.org/bot{token}/{method}"


def send_message(token: str, chat_id: int | str, text: str) -> None:
    """Send plain text (chunked to Telegram's 4096-char limit)."""
    text = text or "(không có nội dung)"
    for i in range(0, len(text), 4000):
        chunk = text[i : i + 4000]
        try:
            requests.post(
                tg_api(token, "sendMessage"),
                json={"chat_id": chat_id, "text": chunk},
                timeout=30,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[send error] {exc}")


def send_typing(token: str, chat_id: int | str) -> None:
    try:
        requests.post(
            tg_api(token, "sendChatAction"),
            json={"chat_id": chat_id, "action": "typing"},
            timeout=10,
        )
    except Exception:  # noqa: BLE001
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Telegram bridge for the Research Agent.")
    parser.add_argument("--provider", choices=["openrouter", "openai", "anthropic", "gemini", "ollama"], required=True)
    parser.add_argument("--model", default=None)
    parser.add_argument("--version", required=True, help="Artifact version label, e.g. v3.")
    parser.add_argument("--system-prompt", type=Path, default=ARTIFACTS_DIR / "system_prompt.md")
    parser.add_argument("--tools", type=Path, default=ARTIFACTS_DIR / "tools.yaml")
    parser.add_argument("--transcripts-dir", type=Path, default=ROOT / "transcripts")
    parser.add_argument("--history-window", type=int, default=5)
    parser.add_argument("--max-tool-rounds", type=int, default=4)
    parser.add_argument("--open", action="store_true", help="Answer ANY chat, not only TELEGRAM_CHAT_ID.")
    parser.add_argument("--backlog", action="store_true", help="Also process messages sent before start.")
    args = parser.parse_args()

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN in .env")
    allowed_chat = None if args.open else os.getenv("TELEGRAM_CHAT_ID")

    system_prompt = args.system_prompt.read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(args.tools)
    openai_tools = to_openai_tools(tool_declarations)
    provider = make_provider(args.provider)
    selected_model = args.model or getattr(provider, "default_model", None)
    artifact_version = build_artifact_version(args.version, args.system_prompt, args.tools)

    # One transcript per bot session.
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(args.version), "telegram", timestamp])
    transcript_path = args.transcripts_dir / f"{transcript_id}.transcript.json"
    transcript: dict[str, Any] = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": args.provider,
        "model": selected_model,
        "system_prompt": str(args.system_prompt),
        "tools": str(args.tools),
        "history_window": args.history_window,
        "max_tool_rounds": args.max_tool_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "channel": "telegram",
        "turns": [],
    }

    histories: dict[int, list[dict[str, str]]] = {}
    offset: int | None = None
    turn_index = 0

    # Skip backlog: fast-forward offset past any messages already queued.
    if not args.backlog:
        try:
            resp = requests.get(tg_api(token, "getUpdates"), params={"timeout": 0}, timeout=30).json()
            for u in resp.get("result", []):
                offset = u["update_id"] + 1
        except Exception as exc:  # noqa: BLE001
            print(f"[backlog skip error] {exc}")

    me = requests.get(tg_api(token, "getMe"), timeout=20).json().get("result", {})
    print(f"🤖 Bot @{me.get('username')} đang chạy. artifact_version={artifact_version.artifact_version}")
    print(f"   Chỉ trả lời chat_id={allowed_chat or 'ANY (--open)'} | Ctrl+C để dừng.")

    while True:
        try:
            resp = requests.get(
                tg_api(token, "getUpdates"),
                params={"timeout": 30, "offset": offset},
                timeout=60,
            ).json()
        except KeyboardInterrupt:
            break
        except Exception as exc:  # noqa: BLE001
            print(f"[poll error] {exc}")
            continue

        for update in resp.get("result", []):
            offset = update["update_id"] + 1
            msg = update.get("message") or update.get("edited_message")
            if not msg:
                continue
            chat = msg.get("chat", {})
            chat_id = chat.get("id")
            text = (msg.get("text") or "").strip()

            if allowed_chat is not None and str(chat_id) != str(allowed_chat):
                send_message(token, chat_id, "Xin lỗi, bot này đang chạy ở chế độ riêng tư.")
                continue
            if not text:
                send_message(token, chat_id, "Mình chỉ xử lý tin nhắn văn bản nhé.")
                continue
            if text in {"/start", "/help"}:
                send_message(token, chat_id, START_MESSAGE)
                continue
            if text == "/reset":
                histories.pop(chat_id, None)
                send_message(token, chat_id, "🧹 Đã xoá lịch sử hội thoại.")
                continue

            print(f"\n[{now_iso()}] {chat.get('first_name') or chat_id}> {text}")
            send_typing(token, chat_id)
            turn_index += 1
            history = histories.setdefault(chat_id, [])
            messages = [
                {"role": "system", "content": system_prompt},
                *trim_history(history, args.history_window),
                {"role": "user", "content": text},
            ]

            turn_record: dict[str, Any] = {
                "turn_index": turn_index,
                "chat_id": chat_id,
                "started_at": now_iso(),
                "user": text,
            }
            try:
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=selected_model,
                    max_tool_rounds=args.max_tool_rounds,
                )
                answer = result.get("assistant_text") or "(không có nội dung)"
                turn_record.update(result)
                history.append({"role": "user", "content": text})
                history.append({"role": "assistant", "content": answer})
                print(f"Agent> {answer[:200]}")
                send_message(token, chat_id, answer)
            except Exception as exc:  # noqa: BLE001
                error = f"{type(exc).__name__}: {exc}"
                turn_record.update({"status": "provider_error", "error": error})
                print(f"ERROR> {error}")
                send_message(token, chat_id, f"⚠️ Lỗi xử lý: {error}")

            turn_record["ended_at"] = now_iso()
            transcript["turns"].append(turn_record)
            write_transcript(transcript_path, transcript)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Bot dừng.")
