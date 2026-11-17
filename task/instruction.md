# Task: Clickstream Sessionization Report

You are given `data/events.csv`, a raw export of user clickstream events from several
regional servers. Write a Python module `solution.py` that exposes:

```python
def sessionize(csv_path: str) -> dict[str, dict]:
    ...
```

It returns a mapping `user_id -> {"sessions": int, "longest_session_s": int, "events": int}`.

## Input format

| column        | description |
|---------------|-------------|
| `event_id`    | unique id of the logical event; the export may contain the same event more than once |
| `user_id`     | string |
| `ts`          | ISO-8601 timestamp **with a UTC offset** (servers in different regions write different offsets) |
| `event_type`  | one of `page_view`, `click`, `purchase`, `logout` |
| `ingested_at` | ISO-8601 UTC timestamp of when the row reached the warehouse |

Rows are **not** guaranteed to be in chronological order.

## Rules

1. **Deduplication.** If several rows share an `event_id`, keep only the row with the
   earliest `ingested_at`. Treat all of them as one event.
2. **Invalid rows.** Drop any row whose `ts` cannot be parsed as an offset-aware ISO-8601
   timestamp (empty, garbage, or missing an offset). Dropping happens *before* deduplication.
3. **Ordering.** A user's events are ordered by their actual instant in time (not by the
   textual timestamp). Ties are broken by `event_id` ascending.
4. **Session boundaries.** A new session starts at an event when either:
   - the gap since the user's previous event is **strictly greater than 30 minutes**, or
   - the user's previous event was a `logout`.

   A `logout` event belongs to the session it ends.
5. **Duration.** A session's duration is the whole number of seconds between its first and
   last event (a single-event session has duration `0`).
6. **Output.** For each user with at least one valid event, report the number of sessions,
   the longest session duration in seconds, and the number of distinct valid events.
   Users with no valid events must not appear.

Use only the Python standard library or pandas.
