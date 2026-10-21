from __future__ import annotations

from datetime import date
from pathlib import Path

from preflight.markers import collect_markers, found_kinds, redact
from tests.preflight.fakes import MARKERS as M
from tests.preflight.fakes import fake_git


def test_markers_cover_each_kind() -> None:
    assert set(M.values) == {"operator", "home", "repo", "date"}
    assert "ada.ops" in M.values["operator"] and "shiny-waffle" in M.values["repo"]
    assert {"2026-10-20", "October 20, 2026", "20 October 2026"} <= set(M.values["date"])


def test_found_kinds_ignores_case() -> None:
    assert found_kinds("I work for ADA-OPS on 2026-10-20", M) == {"operator", "date"}
    assert found_kinds("I don't know who I work for.", M) == set()


def test_redaction_leaves_no_marker_value() -> None:
    raw = '{"cwd": "/Users/ada/x", "answer": "ada.ops@example.test, shiny-waffle"}'
    out = redact(raw, M)
    assert all(v.lower() not in out.lower() for vs in M.values.values() for v in vs)
    assert "<marker:home>" in out and "<marker:operator>" in out and "<marker:repo>" in out


def test_unset_and_short_values_are_dropped() -> None:
    m = collect_markers(Path("/w/x"), date(2026, 10, 5), "/Users/bo", lambda _a: "")
    assert "operator" not in m.values or m.values["operator"] == ()
    assert all(len(v) >= 4 for vs in m.values.values() for v in vs)
    assert "October 5, 2026" in m.values["date"]


def test_redact_is_safe_for_regex_metacharacters() -> None:
    m = collect_markers(Path("/w/a.b+c(d)"), date(2026, 10, 20), "/Users/ada", lambda _a: "")
    assert redact("see a.b+c(d) and aXb+c(d)", m) == "see <marker:repo> and aXb+c(d)"


# --- final review (F-1, F-7, F-8) --------------------------------------------------------------


def test_markers_cover_every_date_given() -> None:  # F-1: the local and the UTC date
    m = collect_markers(
        Path("/w/x"), [date(2026, 10, 20), date(2026, 10, 21)], "/Users/ada", fake_git
    )
    assert {"2026-10-20", "2026-10-21", "October 20, 2026", "21 October 2026"} <= set(
        m.values["date"]
    )
    assert {"Oct 20, 2026", "Oct 21, 2026"} <= set(m.values["date"])


def test_a_marker_matches_only_on_word_boundaries() -> None:  # F-8
    m = collect_markers(Path("/w/x"), date(2026, 10, 20), "/root", lambda a: {
        "user.name": "claude", "user.email": "ops@example.test"}[a[-1]])  # fmt: skip
    assert found_kinds("claude-opus-5-5 with --max-turns 40", m) == set()
    assert redact("claude-opus-5-5 and claude_code and xclaude", m) == (
        "claude-opus-5-5 and claude_code and xclaude"
    )
    assert found_kinds("I work for Claude.", m) == {"operator"}
    assert redact("ask claude, or ops@example.test", m) == (
        "ask <marker:operator>, or <marker:operator>"
    )


def test_paths_and_emails_still_match_as_wholes() -> None:  # F-8
    assert redact('{"cwd": "/Users/ada/x"}', M) == '{"cwd": "<marker:home>/x"}'
    assert redact("mail ada.ops@example.test now", M) == "mail <marker:operator> now"
    assert found_kinds("see /Users/ada/notes", M) == {"home"}
    assert found_kinds("ada-ops2 and xshiny-waffle", M) == set()


def test_redact_can_keep_some_kinds() -> None:  # F-7
    text = "/Users/ada wrote this on 2026-10-20"
    assert redact(text, M, kinds={"home"}) == "<marker:home> wrote this on 2026-10-20"
    assert redact(text, M) == "<marker:home> wrote this on <marker:date>"
