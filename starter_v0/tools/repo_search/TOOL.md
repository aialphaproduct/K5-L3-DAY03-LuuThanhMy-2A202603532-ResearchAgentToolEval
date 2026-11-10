---
name: repo_search
track: new
kind: live_api
provider: GitHub Search API
requires_env: []
inputs: [query, sort, max_results]
outputs: [items]
side_effect: false
---
# repo_search

Search public GitHub repositories using the GitHub Search API.
No API key required for light use (rate-limited without a token).

Params:
- `query` (required): repo/library keyword.
- `sort`: one of `stars`, `forks`, `updated`, `best_match`. Any other value
  returns an error dict without a request.
- `max_results`: cap hits (minimum 1, default 5).

Behaviour notes:
- Empty/whitespace `query` returns zero items without any HTTP call.
- Result items carry `title` (full repo name), `url`, `source`, `summary`
  (description), `stars` and `language`.
- All failures (HTTP 403 rate limit, 422 bad sort, timeouts) return an error
  dict instead of raising - the model must read `error`, not a stack trace.
