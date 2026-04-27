# DebAIte ID Legend

All session-scoped IDs follow the same pattern: a short type prefix followed by a monotonic counter.
Counters live on `MUN._counters` and are issued via `session.next_id(prefix)`.

| Prefix | Object              | Example | Source                        |
|--------|---------------------|---------|-------------------------------|
| `MC`   | Moderated Caucus    | `MC1`   | `general_debate` (motion=mod) |
| `UMC`  | Unmoderated Caucus  | `UMC1`  | `general_debate` (motion=unmod) |
| `P`    | Working Paper       | `P1`    | `process_unmoderated_caucus`  |
| `DR`   | Draft Resolution    | `DR1`   | `process_unmoderated_caucus`  |
| `V`    | Vote                | `V1`    | `vote_draft_resolution`       |

## Cross-references

Some objects keep a pointer back to their origin instead of encoding it in the ID:

- `WorkingPaper.bloc_id` → which bloc drafted it (e.g. `"B1"`)
- `DraftResolution.paper_id` → which working paper it was promoted from (e.g. `"P1"`)

## Bloc IDs

Blocs are formed manually by the chair during unmoderated caucuses. Convention is `B1`, `B2`, ...
They are *not* issued via `next_id` — the chair types them directly when forming blocs.
