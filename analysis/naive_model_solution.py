"""A representative *flawed* model attempt, written to mirror common failure patterns
observed when LLM agents solve this kind of task. Used to demonstrate test failures and
trajectory analysis. Do not treat as a reference.
"""
import pandas as pd


def sessionize(csv_path: str) -> dict[str, dict]:
    df = pd.read_csv(csv_path, dtype=str)
    df = df.dropna(subset=["ts"])
    df = df.drop_duplicates("event_id", keep="last")          # F1: keeps wrong duplicate
    df = df.sort_values(["user_id", "ts"])                     # F2: sorts strings, not instants
    df["t"] = pd.to_datetime(df["ts"], errors="coerce", utc=True)  # F3: naive ts silently treated as UTC
    df = df.dropna(subset=["t"])

    out = {}
    for user, g in df.groupby("user_id"):
        gaps = g["t"].diff()
        new = gaps.isna() | (gaps >= pd.Timedelta(minutes=30))  # F4: >= instead of >
        sid = new.cumsum()                                         # F5: ignores logout rule
        dur = g.groupby(sid)["t"].agg(lambda s: (s.max() - s.min()).total_seconds())
        out[user] = {"sessions": int(sid.max()), "longest_session_s": dur.max(),  # F6: float
                     "events": len(g)}
    return out
