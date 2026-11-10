---
name: notes
track: new
kind: local_knowledge
provider: none (local file)
requires_env: []
inputs: [action, text, title, limit]
outputs: [items]
side_effect: local_file_write
requires_confirmation: false
---
# notes

Agent scratchpad stored in `notes/notes.json` (local file only).

Params:
- `action` (required): `save` or `list`. Any other value returns an error dict.
- `text`: note content for `save`. Empty text returns an error dict and writes
  nothing.
- `title`: optional short title; defaults to a slug of the note text.
- `limit`: how many notes `list` returns (default 10, minimum 1).

Behaviour notes:
- `save` appends `{id, title, text, created_at}` and keeps at most 200 notes.
- `list` returns the newest notes last, each carrying `title`, `text`, `created_at`.
- A corrupt note file is tolerated (behaves like empty).
- All failures (bad action, empty text, disk errors) return an error dict
  instead of raising.
