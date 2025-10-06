from __future__ import annotations

import json

from src.models.game_state import GameState
from src.models.schemas import BranchSchema, TurnResolutionSchema, WorldSetupSchema
from src.services.journal import JournalExporter


def _build_state_with_turn() -> GameState:
    state = GameState.from_world_schema(
        "World",
        WorldSetupSchema(
            opening_scene="Scene",
            initial_problem="Problem",
            npcs=[{"name": "Kai", "description": "", "personality": "", "resistance": 5, "relationship": 0}],
        ),
    )
    resolution = TurnResolutionSchema(
        active_npc={
            "name": "Kai",
            "description": "",
            "personality": "",
            "resistance": 5,
            "relationship": 0,
        },
        npc_response="Sentence one. Sentence two. Sentence three.",
        outcome_type="Success",
        outcome_summary="Win",
        npc_resistance_change=-2,
        npc_relationship_change=1,
        next_problem="Next",
        branches=[BranchSchema(title="A", description="")],
    )
    state.apply_resolution(resolution, "Hey")
    return state


def test_journal_exporter_writes_json(tmp_path) -> None:
    state = _build_state_with_turn()
    exporter = JournalExporter(output_dir=tmp_path)
    path = exporter.export(state)
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["world_setting"] == "World"
    assert len(data["turns"]) == 1
