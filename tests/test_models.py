from __future__ import annotations

from src.models.game_state import GameState, NPCState
from src.models.schemas import BranchSchema, TurnResolutionSchema, WorldSetupSchema


def build_game_state() -> GameState:
    schema = WorldSetupSchema(
        opening_scene="Scene",
        initial_problem="Initial problem",
        npcs=[
            {
                "name": "Alex",
                "description": "",
                "personality": "Stoic",
                "resistance": 4,
                "relationship": 1,
            }
        ],
    )
    return GameState.from_world_schema("Test World", schema)


def test_npc_adjust_clamps_resistance() -> None:
    npc = NPCState(name="Sam", description="", personality="", resistance=1, relationship=0)
    npc.adjust(-5, 3)
    assert npc.resistance == 0
    assert npc.relationship == 3

def test_apply_resolution_updates_state() -> None:
    state = build_game_state()
    resolution = TurnResolutionSchema(
        active_npc={
            "name": "Alex",
            "description": "",
            "personality": "Stoic",
            "resistance": 4,
            "relationship": 1,
        },
        npc_response="Sentence one. Sentence two? Sentence three!",
        outcome_type="Success",
        outcome_summary="You convinced Alex.",
        npc_resistance_change=-1,
        npc_relationship_change=2,
        next_problem="Next dilemma",
        branches=[
            BranchSchema(title="A", description=""),
            BranchSchema(title="B", description=""),
            BranchSchema(title="C", description=""),
        ],
    )
    record, npc = state.apply_resolution(resolution, "Hello")

    assert npc.resistance == 3
    assert npc.relationship == 3
    assert state.current_problem == "Next dilemma"
    assert record.outcome_type == "Success"
    assert state.total_successes == 1
    assert state.pending_branches[0]["title"] == "A"
    summary, recent = state.narrative_context()
    assert "Turn 1" in summary or summary == ""
    assert recent[-1]["npc"] == "Alex"


def test_normalize_deltas_clamps_conflicting_values() -> None:
    state = build_game_state()
    resolution = TurnResolutionSchema(
        active_npc={
            "name": "Alex",
            "description": "",
            "personality": "Stoic",
            "resistance": 4,
            "relationship": 1,
        },
        npc_response="Sentence one. Sentence two. Sentence three.",
        outcome_type="Success",
        outcome_summary="You convinced Alex.",
        npc_resistance_change=2,
        npc_relationship_change=-3,
        next_problem="Next dilemma",
        branches=[BranchSchema(title="A", description="")],
    )
    record, npc = state.apply_resolution(resolution, "Hello")

    assert record.resistance_shift == -1  # forced improvement on success
    assert record.relationship_shift == 1
    assert npc.resistance == 3
    assert npc.relationship == 2


def test_last_active_npc_and_streak() -> None:
    state = build_game_state()
    resolution = TurnResolutionSchema(
        active_npc={
            "name": "Alex",
            "description": "",
            "personality": "Stoic",
            "resistance": 4,
            "relationship": 1,
        },
        npc_response="Sentence one. Sentence two. Sentence three.",
        outcome_type="Success",
        outcome_summary="Win",
        npc_resistance_change=-1,
        npc_relationship_change=2,
        next_problem="Next",
        branches=[BranchSchema(title="A", description="")],
    )
    state.apply_resolution(resolution, "Hello")
    assert state.last_active_npc() == "Alex"
    assert state.consecutive_npc_streak() == ("Alex", 1)
