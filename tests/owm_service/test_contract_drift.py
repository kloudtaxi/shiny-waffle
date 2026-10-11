"""The models mirror owm-decisions.ts at garbanzo 30977cd. The contract's own S22 walk-through
(s22.example.json, generated from s22.example.ts) must parse under extra="forbid"."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, RootModel, ValidationError

from owm_service import models
from owm_service.errors import CannotDecide, NotFound, Refused, Unauthenticated
from owm_service.models import (
    ClearanceRequest,
    ClearanceResponse,
    DecisionRecord,
    DecisionRequest,
    RedeemResponse,
    Refusals,
)

CONTRACT = Path(__file__).resolve().parents[2] / "lab" / "owm_service" / "contract"

EXAMPLES: dict[str, Any] = {
    "ask": DecisionRequest,
    "ask8": ClearanceRequest,
    "v1": DecisionRecord,
    "refused8": ClearanceResponse,
    "v2AfterApproval": DecisionRecord,
    "cleared15": ClearanceResponse,
    "replay": RedeemResponse,
    "afterSpent": ClearanceResponse,
    "laterDecision": DecisionRecord,
    "laterDecisionRefused": ClearanceResponse,
    "secondDecision": Refusals,
    "v2Ratchet": DecisionRecord,
}


def all_examples() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(CONTRACT.joinpath("s22.example.json").read_text())
    return loaded


def example(name: str) -> Any:
    return all_examples()[name]


def test_every_s22_export_is_covered() -> None:
    assert set(all_examples()) == set(EXAMPLES)


@pytest.mark.parametrize("name", EXAMPLES)
def test_s22_example_parses(name: str) -> None:
    EXAMPLES[name].model_validate(example(name))


def test_decision_request_forbids_as_of() -> None:
    with pytest.raises(ValidationError):
        DecisionRequest.model_validate(
            {
                "decision_type": "discount",
                "subject": {"request_id": "DR-9001"},
                "as_of": "2025-09-23",
            }
        )


def test_decision_request_has_exactly_three_fields() -> None:
    assert set(DecisionRequest.model_fields) == {"decision_type", "subject", "submitted"}


def test_unions_discriminate() -> None:
    rec = DecisionRecord.model_validate(example("v1"))
    assert rec.actor.kind == "agent"
    cleared = ClearanceResponse.model_validate(example("cleared15"))
    assert cleared.root.cleared is True
    redeem = RedeemResponse.model_validate(example("replay"))
    assert redeem.root.redeemed is False


def test_extra_field_is_refused_on_nested_models() -> None:
    bad = example("v1")
    bad["actor"]["surprise"] = 1
    with pytest.raises(ValidationError):
        DecisionRecord.model_validate(bad)


def test_all_models_forbid_extra() -> None:
    seen = 0
    for name in dir(models):
        obj = getattr(models, name)
        is_model = isinstance(obj, type) and issubclass(obj, BaseModel)
        if is_model and obj.__module__ == models.__name__ and not issubclass(obj, RootModel):
            assert obj.model_config.get("extra") == "forbid", name
            seen += 1
    assert seen >= 30


def test_errors() -> None:
    assert Refused(422, []).status == 422
    assert NotFound("DEC-0001").what == "DEC-0001"
    assert CannotDecide("jev down").detail == "jev down"
    assert isinstance(Unauthenticated(), Exception)
