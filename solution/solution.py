"""Golden solution for the clickstream sessionization task."""
import csv
from datetime import datetime, timedelta

GAP = timedelta(minutes=30)


def _parse(ts: str):
    try:
        dt = datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return None
    return dt if dt.tzinfo is not None and dt.utcoffset() is not None else None


def sessionize(csv_path: str) -> dict[str, dict]:
    # Rules 1-2: drop unparseable rows, then dedupe on earliest ingestion.
    best: dict[str, tuple] = {}
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            when = _parse(row["ts"])
            if when is None:
                continue
            ingested = datetime.fromisoformat(row["ingested_at"])
            cur = best.get(row["event_id"])
            if cur is None or ingested < cur[0]:
                best[row["event_id"]] = (ingested, row["user_id"], when, row["event_type"])

    by_user: dict[str, list] = {}
    for eid, (_, user, when, etype) in best.items():
        by_user.setdefault(user, []).append((when, eid, etype))

    report = {}
    for user, events in by_user.items():
        events.sort()  # aware datetimes compare by instant; ties by event_id (rule 3)
        sessions, longest = 0, 0
        start = prev = prev_type = None
        for when, _, etype in events:
            if prev is None or when - prev > GAP or prev_type == "logout":
                if start is not None:
                    longest = max(longest, int((prev - start).total_seconds()))
                sessions += 1
                start = when
            prev, prev_type = when, etype
        longest = max(longest, int((prev - start).total_seconds()))
        report[user] = {"sessions": sessions, "longest_session_s": longest, "events": len(events)}
    return report
