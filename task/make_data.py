"""Deterministically generate task/data/events.csv.

Hand-written edge cases are mixed with seeded random traffic, then the rows are shuffled.
"""
import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT = Path(__file__).parent / "data" / "events.csv"
UTC = timezone.utc
IST = timezone(timedelta(hours=5, minutes=30))
PST = timezone(timedelta(hours=-8))
BASE = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)

rows: list[dict] = []
_seq = 0


def add(user, when, etype="page_view", tz=UTC, event_id=None, ingest_delay_s=5):
    global _seq
    _seq += 1
    eid = event_id or f"e{_seq:05d}"
    rows.append({
        "event_id": eid,
        "user_id": user,
        "ts": when.astimezone(tz).isoformat() if isinstance(when, datetime) else when,
        "event_type": etype,
        "ingested_at": ((when if isinstance(when, datetime) else BASE)
                        + timedelta(seconds=ingest_delay_s)).astimezone(UTC).isoformat(),
    })
    return eid


# --- u_boundary: gap of exactly 30:00 continues, 30:01 splits -> 2 sessions -----------
t = BASE
add("u_boundary", t)
add("u_boundary", t + timedelta(minutes=30))                       # same session
add("u_boundary", t + timedelta(minutes=60, seconds=1))            # new session

# --- u_offsets: same instants written in different offsets ------------------------------
# Textually, the IST string sorts *after* the PST one though it is earlier in time.
t = BASE + timedelta(hours=2)
add("u_offsets", t, tz=IST)
add("u_offsets", t + timedelta(minutes=20), tz=PST)
add("u_offsets", t + timedelta(minutes=40), tz=IST)                # one 40-min session

# --- u_logout: logout forces a split even with tiny gap --------------------------------
t = BASE + timedelta(hours=4)
add("u_logout", t)
add("u_logout", t + timedelta(minutes=5), "logout")
add("u_logout", t + timedelta(minutes=6))                          # new session
add("u_logout", t + timedelta(minutes=10), "purchase")

# --- u_dupes: duplicate event ids; later ingestion carries a different (wrong) ts -------
t = BASE + timedelta(hours=6)
add("u_dupes", t, event_id="dupA", ingest_delay_s=2)
add("u_dupes", t + timedelta(hours=3), event_id="dupA", ingest_delay_s=50)  # discard
add("u_dupes", t + timedelta(minutes=25), event_id="dupB")
add("u_dupes", t + timedelta(minutes=25), event_id="dupB", ingest_delay_s=9)  # exact dup

# --- u_invalid: only bad timestamps -> must not appear ---------------------------------
add("u_invalid", "")
add("u_invalid", "not-a-date")
add("u_invalid", "2026-03-01T10:00:00")                            # naive, no offset

# --- u_mixed_invalid: bad row between two valid rows must not bridge/split anything ----
t = BASE + timedelta(hours=8)
add("u_mixed_invalid", t)
add("u_mixed_invalid", "garbage")
add("u_mixed_invalid", t + timedelta(minutes=45))                  # 2 sessions

# --- u_tie: identical instants, logout ordering resolved by event_id -------------------
t = BASE + timedelta(hours=10)
add("u_tie", t, event_id="t1")
add("u_tie", t + timedelta(minutes=1), "logout", event_id="t2")
add("u_tie", t + timedelta(minutes=1), event_id="t3")              # after logout -> new session

# --- random background traffic ---------------------------------------------------------
rng = random.Random(1729)
for u in range(12):
    user = f"user_{u:02d}"
    t = BASE + timedelta(minutes=rng.randint(0, 600))
    for _ in range(rng.randint(3, 25)):
        t += timedelta(seconds=rng.choice([rng.randint(5, 900), rng.randint(1500, 2100),
                                           rng.randint(3600, 9000)]))
        etype = rng.choices(["page_view", "click", "purchase", "logout"], [6, 5, 1, 1])[0]
        add(user, t, etype, tz=rng.choice([UTC, IST, PST]))
        if rng.random() < 0.1:   # replayed duplicate with later ingestion
            r = dict(rows[-1]); r["ingested_at"] = (t + timedelta(minutes=10)).isoformat()
            rows.append(r)

rng.shuffle(rows)
OUT.parent.mkdir(exist_ok=True)
with OUT.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["event_id", "user_id", "ts", "event_type", "ingested_at"])
    w.writeheader()
    w.writerows(rows)
print(f"wrote {len(rows)} rows to {OUT}")
