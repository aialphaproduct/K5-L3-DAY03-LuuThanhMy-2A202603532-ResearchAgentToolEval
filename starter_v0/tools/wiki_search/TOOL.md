---
name: wiki_search
track: new
kind: live_api
provider: Wikipedia MediaWiki API
requires_env: []
inputs: [query, language, max_results]
outputs: [items]
side_effect: false
---
# wiki_search

Search the Wikipedia MediaWiki API for article titles with snippets.
No API key required.

Params:
- `query` (required): the concept/topic to look up.
- `language`: only `en` or `vi`. Any other value returns an error dict
  (never a crash and never a request).
- `max_results`: cap hits (minimum 1, default 5).

Behaviour notes:
- Empty/whitespace `query` returns zero items without any HTTP call.
- HTML tags inside MediaWiki snippets are stripped; `&quot;`/`&amp;` are decoded.
- Result items carry `title`, `url` (the Wikipedia page URL), `source`, `summary`.
- All failures (HTTP errors, bad language) return an error dict instead of raising.
