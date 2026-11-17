"""Unit tests. Run against any candidate via: SOLUTION=path/to/solution.py pytest tests/"""
import importlib.util
import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "task" / "data" / "events.csv"
SOLUTION = Path(os.environ.get("SOLUTION", ROOT / "solution" / "solution.py"))


@pytest.fixture(scope="session")
def report():
    spec = importlib.util.spec_from_file_location("candidate", SOLUTION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.sessionize(str(DATA))


def test_exact_30min_gap_continues_session(report):
    assert report["u_boundary"] == {"sessions": 2, "longest_session_s": 1800, "events": 3}


def test_mixed_utc_offsets_ordered_by_instant(report):
    assert report["u_offsets"] == {"sessions": 1, "longest_session_s": 2400, "events": 3}


def test_logout_ends_session(report):
    assert report["u_logout"] == {"sessions": 2, "longest_session_s": 300, "events": 4}


def test_dedup_keeps_earliest_ingested_row(report):
    assert report["u_dupes"] == {"sessions": 1, "longest_session_s": 1500, "events": 2}


def test_user_with_only_invalid_rows_is_omitted(report):
    assert "u_invalid" not in report


def test_invalid_row_does_not_affect_neighbours(report):
    assert report["u_mixed_invalid"] == {"sessions": 2, "longest_session_s": 0, "events": 2}


def test_tie_broken_by_event_id(report):
    assert report["u_tie"] == {"sessions": 2, "longest_session_s": 60, "events": 3}


def test_return_types_are_plain_ints(report):
    for stats in report.values():
        assert all(type(v) is int for v in stats.values()), stats


def _run_on(tmp_path, lines):
    p = tmp_path / "mini.csv"
    p.write_text("event_id,user_id,ts,event_type,ingested_at\n" + "\n".join(lines) + "\n")
    spec = importlib.util.spec_from_file_location("candidate_mini", SOLUTION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.sessionize(str(p))


def test_dedup_independent_of_row_order(tmp_path):
    # The wrong duplicate is physically last *and* first-ingested row comes second in file.
    r = _run_on(tmp_path, [
        "a,u,2026-01-01T10:00:00+00:00,click,2026-01-01T10:00:05+00:00",
        "b,u,2026-01-01T10:10:00+00:00,click,2026-01-01T10:10:05+00:00",
        "b,u,2026-01-01T15:00:00+00:00,click,2026-01-01T16:00:00+00:00",
    ])
    assert r == {"u": {"sessions": 1, "longest_session_s": 600, "events": 2}}


def test_naive_timestamp_is_invalid(tmp_path):
    r = _run_on(tmp_path, [
        "a,u,2026-01-01T10:00:00+00:00,click,2026-01-01T10:00:05+00:00",
        "b,u,2026-01-01T10:10:00,click,2026-01-01T10:10:05+00:00",
        "c,v,2026-01-01T10:10:00,click,2026-01-01T10:10:05+00:00",
    ])
    assert r == {"u": {"sessions": 1, "longest_session_s": 0, "events": 1}}


def test_background_users_match_reference(report):
    expected = json.loads((ROOT / "tests" / "expected_background.json").read_text())
    got = {u: report.get(u) for u in expected}
    assert got == expected
