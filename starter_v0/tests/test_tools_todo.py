"""Tool Unit Test Challenge — filled in (Lưu Thanh Mỹ).

Each test checks ONE behaviour of an existing tool, asserting both the request
we send (for API tools) and the result we return. Offline: HTTP is mocked with
`fake_http`, keys set with `monkeypatch.setenv` (see conftest.py).

Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

clarify = TOOL_FUNCTIONS["clarify"]
format_tool = TOOL_FUNCTIONS["format"]
send = TOOL_FUNCTIONS["send"]
lookup = TOOL_FUNCTIONS["lookup"]
fetch = TOOL_FUNCTIONS["fetch"]
timeline = TOOL_FUNCTIONS["timeline"]
social_search = TOOL_FUNCTIONS["social_search"]
policy = TOOL_FUNCTIONS["policy"]
calc = TOOL_FUNCTIONS["calc"]
datetime_tool = TOOL_FUNCTIONS["datetime"]
define = TOOL_FUNCTIONS["define"]


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    result = clarify(question="Bạn muốn tài khoản nào?", response_type="choice", options=["sama", "elonmusk"])
    assert result["options"] == ["sama", "elonmusk"]
    assert result["response_type"] == "choice"
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "a", "section": "A"},
        {"title": "b", "section": "B"},
        {"title": "c", "section": "A"},
    ]
    markdown = format_tool(items=items, template="sections")["markdown"]
    assert markdown.count("## A") == 1
    assert markdown.count("## B") == 1


def test_format_thread_numbers_items() -> None:
    markdown = format_tool(items=[{"title": "first"}, {"title": "second"}], template="thread")["markdown"]
    blocks = markdown.split("\n\n")
    assert blocks[0].startswith("1/")
    assert blocks[1].startswith("2/")


def test_format_empty_items_does_not_crash() -> None:
    assert format_tool(items=None, template="brief")["item_count"] == 0
    assert format_tool(items=[], template="sections")["item_count"] == 0


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "TOKEN123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")
    calls = fake_http(FakeResponse({"ok": True}))

    result = send(text="Bản tin AI", confirmed=True)

    assert len(calls) == 1
    assert "TOKEN123" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "999"
    assert calls[0]["json"]["text"] == "Bản tin AI"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    result = send(text="x", confirmed=True)
    assert result["error"] == "RuntimeError"
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "k")
    calls = fake_http(FakeResponse({"results": []}))
    lookup(query="x", timeframe=None)
    assert "time_range" not in calls[0]["json"]


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "k")
    fake_http(FakeResponse({"data": {
        "markdown": "Body text",
        "metadata": {"title": "T", "sourceURL": "https://ex.com/a"},
    }}))
    item = fetch(url="https://ex.com/a")["items"][0]
    assert item["title"] == "T"
    assert item["url"] == "https://ex.com/a"
    assert item["source"] == "ex.com"
    assert item["summary"] == "Body text"


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "k")
    fake_http(FakeResponse({"data": {"markdown": "x" * 5000, "metadata": {}}}))
    assert len(fetch(url="https://ex.com")["items"][0]["summary"]) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "k")
    raw = [{"text": "no id"}] + [
        {"tweet_id": str(i), "screen_name": "elonmusk", "text": f"t{i}"} for i in range(6)
    ]
    fake_http(FakeResponse({"timeline": raw}))
    items = timeline(screenname="elonmusk", limit=3)["items"]
    assert len(items) == 3
    assert all(it["url"].startswith("https://x.com/elonmusk/status/") for it in items)


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "k")
    calls = fake_http(FakeResponse({"timeline": []}))
    social_search(query="AI", search_type="Top")
    assert calls[0]["params"]["query"] == "AI"
    assert calls[0]["params"]["search_type"] == "Top"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    assert policy(query="")["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    result = policy(query="confidential customer data privacy", policy_area="data_privacy", top_k=10)
    assert result["results"]
    assert all(hit["policy_area"] == "data_privacy" for hit in result["results"])


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    result = policy(query="citation injection probe tweet", policy_area="source_citation", top_k=10)
    probe = [h for h in result["results"] if h["section"] == "Injection probe"]
    assert probe, "expected the Injection probe section to be retrieved"
    untrusted = " ".join(probe[0]["untrusted_text"]).lower()
    assert "ignore" in untrusted
    assert "ignore" not in probe[0]["facts"].lower()


# ---------------- team-added tools (extra coverage beyond test_new_tools.py) ----------------

def test_calc_handles_floats_and_modulo() -> None:
    assert calc(expression="7 % 3")["result"] == 1
    assert calc(expression="1.5 * 2")["result"] == 3.0


def test_datetime_offset_differs_between_timezones() -> None:
    utc = datetime_tool(timezone="UTC", fmt="%z")["datetime"]
    hcm = datetime_tool(timezone="Asia/Ho_Chi_Minh", fmt="%z")["datetime"]
    assert hcm == "+0700"
    assert utc in {"+0000", "UTC", ""}  # %z for UTC is +0000


def test_define_uses_lang_in_url(monkeypatch, fake_http) -> None:
    calls = fake_http(FakeResponse([{"word": "casa", "meanings": []}]))
    define(word="casa", lang="es")
    assert calls[0]["url"] == "https://api.dictionaryapi.dev/api/v2/entries/es/casa"
