"""Unit tests for the team-added tools (Lưu Thanh Mỹ): calc, datetime, wiki, define.

≥3 tests per tool: happy path, bad/absent input from the model, failure path.
Offline: network tools are mocked with `fake_http` (see conftest.py).
"""
from __future__ import annotations

import re

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

calc = TOOL_FUNCTIONS["calc"]
datetime_tool = TOOL_FUNCTIONS["datetime"]
wiki = TOOL_FUNCTIONS["wiki"]
define = TOOL_FUNCTIONS["define"]


# ---------------- calc (pure local) ----------------

def test_calc_evaluates_arithmetic_with_precedence() -> None:
    assert calc(expression="2+3*4")["result"] == 14
    assert calc(expression="(2+3)*4")["result"] == 20
    assert calc(expression="2**10")["result"] == 1024


def test_calc_rejects_non_arithmetic_input() -> None:
    # Empty, code injection, and a dangling operator must all return error dicts, not raise.
    assert calc(expression="")["error"] == "ValueError"
    assert "error" in calc(expression="__import__('os').system('ls')")
    assert "error" in calc(expression="2 +")


def test_calc_division_by_zero_returns_error_dict() -> None:
    result = calc(expression="1/0")
    assert result["error"] == "ZeroDivisionError"
    assert "tool" in result  # error dict shape from _shared.err


# ---------------- datetime (pure local) ----------------

def test_datetime_returns_structured_now_for_valid_tz() -> None:
    result = datetime_tool(timezone="UTC")
    assert result["timezone"] == "UTC"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", result["date"])
    assert re.fullmatch(r"\d{2}:\d{2}:\d{2}", result["time"])
    assert result["weekday"]


def test_datetime_invalid_timezone_returns_error_dict() -> None:
    result = datetime_tool(timezone="Not/AZone")
    assert "error" in result
    assert result["tool"] == "current_datetime"


def test_datetime_custom_format_and_default_tz() -> None:
    year = datetime_tool(timezone="UTC", fmt="%Y")["datetime"]
    assert re.fullmatch(r"\d{4}", year)
    # Empty timezone falls back to UTC instead of crashing.
    assert datetime_tool(timezone="")["timezone"] == "UTC"


# ---------------- wiki (live API, mocked) ----------------

def test_wiki_sends_request_and_maps_summary(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "title": "Artificial intelligence",
        "extract": "AI is intelligence by machines. It studies agents. A third sentence. A fourth.",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Artificial_intelligence"}},
    }))
    result = wiki(title="Artificial intelligence", sentences=2)

    assert calls[0]["url"].startswith("https://en.wikipedia.org/api/rest_v1/page/summary/")
    assert result["title"] == "Artificial intelligence"
    assert result["url"] == "https://en.wikipedia.org/wiki/Artificial_intelligence"
    assert result["source"] == "en.wikipedia.org"
    assert result["summary"].count(". ") <= 1  # trimmed to ~2 sentences


def test_wiki_empty_title_returns_error_without_network(fake_http) -> None:
    calls = fake_http(FakeResponse({}))
    result = wiki(title="")
    assert result["error"] == "ValueError"
    assert calls == []


def test_wiki_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=404))
    assert wiki(title="Nonexistent page xyz")["error"] == "HTTPError"


# ---------------- define (live API, mocked) ----------------

def test_define_maps_meanings(fake_http) -> None:
    calls = fake_http(FakeResponse([{
        "word": "serendipity",
        "phonetic": "/ˌsɛɹənˈdɪpɪti/",
        "meanings": [{"partOfSpeech": "noun", "definitions": [
            {"definition": "A fortunate happenstance."},
            {"definition": "Luck that takes the form of finding valuable things."},
        ]}],
    }]))
    result = define(word="serendipity")

    assert calls[0]["url"] == "https://api.dictionaryapi.dev/api/v2/entries/en/serendipity"
    assert result["word"] == "serendipity"
    assert result["meanings"][0]["part_of_speech"] == "noun"
    assert len(result["meanings"][0]["definitions"]) == 2


def test_define_empty_word_returns_error_without_network(fake_http) -> None:
    calls = fake_http(FakeResponse([]))
    result = define(word="   ")
    assert result["error"] == "ValueError"
    assert calls == []


def test_define_unknown_word_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=404))
    assert define(word="asdfqwerzxcv")["error"] == "HTTPError"
