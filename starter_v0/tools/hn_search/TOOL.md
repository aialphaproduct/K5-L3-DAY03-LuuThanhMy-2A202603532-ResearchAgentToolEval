---
name: hn_search
track: new
kind: live_api
provider: Hacker News Algolia API
requires_env: []
inputs: [query, tag, max_results]
outputs: [items]
side_effect: false
---
# hn_search

Search Hacker News stories and discussions via the public Algolia API.
No API key required.

Params:
- `query` (required): topic keyword.
- `tag`: one of `story`, `comment`, `ask_hn`, `show_hn` (default `story`). An
  out-of-enum tag is ignored (falls back to no tag filter) instead of failing.
- `max_results`: cap hits (minimum 1, default 5).

Behaviour notes:
- Empty/whitespace `query` returns zero items without any HTTP call.
- Hits without `objectID` are skipped.
- Result items carry `title`, `url`, `source`, `summary`, `points` and `type`.
- All failures (HTTP errors, timeouts) return an error dict instead of raising.
