from __future__ import annotations

import pytest

from src.models.schemas import BranchSchema, TurnResolutionSchema
from src.services.gpt_client import GPTClient


def test_strip_code_fences_keeps_plain_text() -> None:
    text = "{\"key\": 1}"
    assert GPTClient._strip_code_fences(text) == text


def test_strip_code_fences_handles_fenced_json() -> None:
    fenced = """```json
{\"key\": 1}
```"""
    assert GPTClient._strip_code_fences(fenced) == '{"key": 1}'


def test_extract_first_json_handles_embedded_text() -> None:
    text = "Noise {\"key\": 1} trailing"
    extracted = GPTClient._extract_first_json(text)
    assert extracted == '{"key": 1}'


def test_safe_json_recovers_from_fenced_content() -> None:
    content = """```\n{\"value\": 10}\n```"""
    parsed = GPTClient._safe_json(content)
    assert parsed == {"value": 10}


def test_enforce_constraints_truncates_and_validates() -> None:
    schema = TurnResolutionSchema(
        active_npc={
            "name": "NPC",
            "description": "",
            "personality": "",
            "resistance": 5,
            "relationship": 0,
        },
        npc_response="One. Two. Three. Four. Five.",
        outcome_type="Alternative",
        outcome_summary="Summary",
        npc_resistance_change=0,
        npc_relationship_change=0,
        next_problem="Next",
        branches=[
            BranchSchema(title="One", description=""),
            BranchSchema(title="Two", description=""),
            BranchSchema(title="Two", description="Duplicate"),
            BranchSchema(title="Three", description=""),
        ],
    )
    GPTClient._enforce_constraints(schema)
    assert schema.npc_response.count('.') <= 4
    assert len(schema.branches) == 3


def test_enforce_constraints_raises_on_short_response() -> None:
    schema = TurnResolutionSchema(
        active_npc={
            "name": "NPC",
            "description": "",
            "personality": "",
            "resistance": 5,
            "relationship": 0,
        },
        npc_response="Only one sentence.",
        outcome_type="Alternative",
        outcome_summary="Summary",
        npc_resistance_change=0,
        npc_relationship_change=0,
        next_problem="Next",
        branches=[BranchSchema(title="One", description="")],
    )
    with pytest.raises(RuntimeError):
        GPTClient._enforce_constraints(schema)
