"""Tool Unit Test Challenge - IMPLEMENTED.

Rules kept from the starter:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeResponse  # noqa: F401
from tools import TOOL_FUNCTIONS
from tools.notes import tool as notes_module
from tools.notes.tool import NOTES_PATH

TODO = "TODO(student): implement this test"  # kept for reference; no stubs remain

ask_user = TOOL_FUNCTIONS["clarify"]
format_tool = TOOL_FUNCTIONS["format"]
send_tool = TOOL_FUNCTIONS["send"]
lookup_tool = TOOL_FUNCTIONS["lookup"]
fetch_tool = TOOL_FUNCTIONS["fetch"]
timeline_tool = TOOL_FUNCTIONS["timeline"]
social_search_tool = TOOL_FUNCTIONS["social_search"]
policy_tool = TOOL_FUNCTIONS["policy"]
hn_search_tool = TOOL_FUNCTIONS["hn_search"]
wiki_search_tool = TOOL_FUNCTIONS["wiki_search"]
repo_search_tool = TOOL_FUNCTIONS["repo_search"]
notes_tool = TOOL_FUNCTIONS["notes"]


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    result = ask_user(
        question="Bạn muốn đọc nguồn nào?",
        response_type="choice",
        options=["blog oficial", "tweet", "HN discussion"],
    )
    assert result["options"] == ["blog oficial", "tweet", "HN discussion"]
    assert result["awaiting_user"] is True
    assert result["response_type"] == "choice"


def test_clarify_text_defaults_to_awaiting_user() -> None:
    result = ask_user(question="URL nào vậy bạn?")
    assert result["options"] == []
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "A1", "url": "https://a.io/1", "section": "A"},
        {"title": "B1", "url": "https://b.io/1", "section": "B"},
        {"title": "A2", "url": "https://a.io/2", "section": "A"},
    ]
    markdown = format_tool(items=items, template="sections")["markdown"]
    assert markdown.count("## A") == 1
    assert markdown.count("## B") == 1
    assert markdown.index("## A") < markdown.index("## B")


def test_format_thread_numbers_items() -> None:
    items = [
        {"title": "Mot", "url": "https://x.io/1"},
        {"title": "Hai", "url": "https://x.io/2"},
    ]
    markdown = format_tool(items=items, template="thread")["markdown"]
    assert "1/ Mot" in markdown
    assert "2/ Hai" in markdown


def test_format_empty_items_does_not_crash() -> None:
    for items in (None, []):
        result = format_tool(items=items, template="sections")
        assert result["item_count"] == 0
        assert isinstance(result["markdown"], str)


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token-123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100chat")
    calls = fake_http(FakeResponse({"ok": True}))

    result = send_tool(text="Bản tin AI", confirmed=True)

    assert result["status"] == "sent"
    assert len(calls) == 1
    assert "bot-token-123" in calls[0]["url"]
    assert calls[0]["json"] == {"chat_id": "-100chat", "text": "Bản tin AI", "parse_mode": "Markdown"}
    assert "sendMessage" in calls[0]["url"]


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))

    result = send_tool(text="Bản tin AI", confirmed=True)

    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]
    assert calls == []  # nothing was sent anywhere


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))

    result = lookup_tool(query="AI", timeframe=None)

    assert "time_range" not in calls[0]["json"]
    assert result["timeframe"] is None


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    fake_http(FakeResponse({
        "data": {
            "markdown": "# Hello world",
            "metadata": {"title": "T", "sourceURL": "https://example.com/x"},
        }
    }))

    result = fetch_tool(url="https://example.com/x")
    item = result["items"][0]

    assert item["title"] == "T"
    assert item["url"] == "https://example.com/x"
    assert item["source"] == "example.com"
    assert item["summary"] == "# Hello world"


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    fake_http(FakeResponse({"data": {"markdown": "x" * 5000, "metadata": {}}}))

    result = fetch_tool(url="https://example.com/long")

    assert len(result["items"][0]["summary"]) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    valid = [{"tweet_id": str(i), "screen_name": "sama", "text": f"tweet {i}"} for i in range(6)]
    payload = {"timeline": [{"text": "no id here"}, *valid]}
    fake_http(FakeResponse(payload))

    result = timeline_tool(screenname="sama", limit=3)

    assert len(result["items"]) == 3
    for item in result["items"]:
        assert item["url"].startswith("https://x.com/sama/status/")
        assert item["source"] == "@sama"


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    calls = fake_http(FakeResponse({"timeline": []}))

    social_search_tool(query="OpenAI", search_type="Top")
    assert calls[0]["url"].endswith("/search.php")
    assert calls[0]["params"]["query"] == "OpenAI"
    assert calls[0]["params"]["search_type"] == "Top"

    social_search_tool(query="GPT-5")
    assert calls[1]["params"]["search_type"] == "Latest"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    result = policy_tool(query="   ")
    assert result["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    result = policy_tool(query="confidential customer data redact PII", policy_area="data_privacy")

    assert len(result["results"]) > 0
    for hit in result["results"]:
        assert hit["policy_area"] == "data_privacy"


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    result = policy_tool(query="injection probe citation", policy_area="source_citation", top_k=5)

    probe_hits = [hit for hit in result["results"] if hit["section"] == "Injection probe"]
    assert probe_hits, "the Injection probe section must be retrievable"
    hit = probe_hits[0]
    assert hit["facts"] == ""  # quoted instruction line is not treated as a fact
    assert hit["untrusted_text"], "instruction-like line must land in untrusted_text"
    assert "ignore" in " ".join(hit["untrusted_text"]).lower()


# ---------------- hn_search (team tool) ----------------

def test_hn_search_sends_expected_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))
    hn_search_tool(query="LLM agents", tag="story", max_results=4)
    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search"
    assert calls[0]["params"]["query"] == "LLM agents"
    assert calls[0]["params"]["tags"] == "story"
    assert calls[0]["params"]["hitsPerPage"] == 4


def test_hn_search_maps_items_and_falls_back_to_hn_url(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": [
        {"objectID": "101", "title": "Show HN: Foo", "url": "https://foo.dev", "story_text": "text here", "points": 42},
        {"objectID": "102", "title": "Bare story"},
        {"objectID": None, "title": "skipped"},
    ]}))

    result = hn_search_tool(query="foo", max_results=5)

    assert "error" not in result, result.get("error")
    assert len(result["items"]) == 2
    assert result["items"][0]["url"] == "https://foo.dev"
    assert result["items"][0]["points"] == 42
    assert result["items"][1]["url"] == "https://news.ycombinator.com/item?id=102"


def test_hn_search_empty_query_makes_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))

    result = hn_search_tool(query="   ")

    assert result["items"] == []
    assert calls == []


def test_hn_search_out_of_enum_tag_is_ignored_not_crash(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": [{"objectID": "1", "title": "ok"}]}))

    result = hn_search_tool(query="foo", tag="trending")

    assert "tags" not in calls[0]["params"]
    assert "error" not in result


def test_hn_search_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=429))

    result = hn_search_tool(query="foo")

    assert result["error"] == "HTTPError"


# ---------------- wiki_search (team tool) ----------------

def test_wiki_search_happy_path_strips_html_and_builds_url(fake_http) -> None:
    calls = fake_http(FakeResponse({"query": {"search": [
        {"title": "Retrieval-augmented generation", "snippet": "<span class=&quot;x&quot;>RAG is a technique</span>"},
    ]}}))

    result = wiki_search_tool(query="RAG", language="en", max_results=3)

    assert calls[0]["url"] == "https://en.wikipedia.org/w/api.php"
    assert calls[0]["params"]["list"] == "search"
    assert calls[0]["params"]["srlimit"] == 3
    assert result["items"][0]["title"] == "Retrieval-augmented generation"
    assert result["items"][0]["summary"] == "RAG is a technique"
    assert result["items"][0]["url"] == "https://en.wikipedia.org/wiki/Retrieval-augmented_generation"


def test_wiki_search_empty_query_makes_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"query": {"search": []}}))

    result = wiki_search_tool(query=" ")

    assert result["items"] == []
    assert calls == []


def test_wiki_search_unsupported_language_returns_error_dict(fake_http) -> None:
    calls = fake_http(FakeResponse({"query": {"search": []}}))

    result = wiki_search_tool(query="RAG", language="fr")

    assert result["error"] == "ValueError"
    assert calls == []


def test_wiki_search_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=500))

    result = wiki_search_tool(query="RAG")

    assert result["error"] == "HTTPError"


# ---------------- repo_search (team tool) ----------------

def test_repo_search_happy_path_maps_repos(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "total_count": 1,
        "items": [{
            "full_name": "stanfordnlp/dspy",
            "html_url": "https://github.com/stanfordnlp/dspy",
            "description": "Framework for programming with LMs",
            "stargazers_count": 9000,
            "language": "Python",
        }],
    }))

    result = repo_search_tool(query="DSPy", sort="stars", max_results=2)

    assert calls[0]["url"] == "https://api.github.com/search/repositories"
    assert calls[0]["params"]["q"] == "DSPy"
    assert calls[0]["params"]["sort"] == "stars"
    assert calls[0]["params"]["per_page"] == 2
    item = result["items"][0]
    assert item["title"] == "stanfordnlp/dspy"
    assert item["url"] == "https://github.com/stanfordnlp/dspy"
    assert item["stars"] == 9000
    assert item["language"] == "Python"


def test_repo_search_empty_query_makes_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"items": []}))

    result = repo_search_tool(query="")

    assert result["items"] == []
    assert calls == []


def test_repo_search_out_of_enum_sort_returns_error_dict(fake_http) -> None:
    calls = fake_http(FakeResponse({"items": []}))

    result = repo_search_tool(query="dspy", sort="hotness")

    assert result["error"] == "ValueError"
    assert calls == []


def test_repo_search_rate_limit_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=403))

    result = repo_search_tool(query="dspy")

    assert result["error"] == "HTTPError"


# ---------------- notes (team tool, local file write) ----------------

@pytest.fixture
def notes_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "notes.json"
    monkeypatch.setattr(notes_module, "NOTES_PATH", path)
    return path


def test_notes_save_appends_entry_and_writes_local_file(notes_path: Path) -> None:
    result = notes_tool(action="save", text="ilya says: keep digests short", title="lesson")

    assert "error" not in result
    assert result["saved"]["title"] == "lesson"
    assert result["saved"]["id"] == 1
    assert notes_path.exists()
    assert "keep digests short" in notes_path.read_text(encoding="utf-8")


def test_notes_list_returns_saved_notes_newest_last(notes_path: Path) -> None:
    notes_tool(action="save", text="first")
    notes_tool(action="save", text="second")

    result = notes_tool(action="list")

    assert result["note_count"] == 2
    assert [item["text"] for item in result["items"]] == ["first", "second"]
    assert "created_at" in result["items"][1]


def test_notes_bad_action_returns_error_dict(notes_path: Path) -> None:
    result = notes_tool(action="delete", text="x")
    assert result["error"] == "ValueError"
    assert "Unsupported action" in result["message"]
    assert not notes_path.exists()


def test_notes_save_with_empty_text_returns_error_dict_and_writes_nothing(notes_path: Path) -> None:
    result = notes_tool(action="save", text="   ")
    assert result["error"] == "ValueError"
    assert "text is empty" in result["message"]
    assert not notes_path.exists()
