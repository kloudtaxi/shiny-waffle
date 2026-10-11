"""Registrar refusals carry optional hints (G-44): `unmatched` (RR-6, RR-7) and `fix` (RR-10).
Neither changes `str(e)` or `e.rule`."""

from __future__ import annotations

from typing import Any

import pytest

from ._registrar import CHECK, registrar


def refuse(ch: dict[str, Any], text: str, acting: set[str]) -> Any:
    with pytest.raises(registrar.RefusedError) as info:
        registrar.apply(registrar.State.bootstrap("base"), ch, text, acting)
    return info.value


def test_c08_style_paraphrase_names_the_unmatched_phrase() -> None:
    ch, text = CHECK.exception_edge()
    paraphrased = text.replace("does not grant approval authority", "grants no approval authority")
    assert paraphrased != text
    e = refuse(ch, paraphrased, {"EMP-200", "EMP-300"})
    assert e.rule == "RR-6" and e.unmatched == "does not grant approval authority"
    assert str(e) == "RR-6: terms say it grants no approval authority; the text doesn't"
    assert e.fix is None


def test_rr10_offers_the_supersession() -> None:
    t27 = CHECK.text_2027_credit().replace("2027-01-01", "2026-12-31")
    ch = CHECK.credit_2027(relations=[], effective_from="2026-12-31")
    e = refuse(ch, t27, {"EMP-401", "EMP-402"})
    assert e.rule == "RR-10"
    assert e.fix == {"relations": [{"type": "supersedes", "target": "CREDIT-POLICY-2026"}]}
    assert e.unmatched is None


def test_rr7_names_the_unstated_date() -> None:
    ch = CHECK.credit_2027(effective_to="2028-12-31")
    e = refuse(ch, CHECK.text_2027_credit(), {"EMP-401", "EMP-402"})
    assert e.rule == "RR-7" and e.unmatched == "2028-12-31"


def test_hints_default_to_none() -> None:
    e = registrar.RefusedError("RR-1", "x")
    assert (e.unmatched, e.fix) == (None, None) and str(e) == "RR-1: x"
