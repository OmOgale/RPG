from __future__ import annotations

from unittest.mock import MagicMock

from src.controllers.game_controller import GameController
from src.models.game_state import GameState
from src.models.schemas import BranchSchema, TurnResolutionSchema, WorldSetupSchema


class FakeGPTClient:
    def __init__(self) -> None:
        self.turn_calls: list[str] = []

    def generate_world(self, setting: str) -> WorldSetupSchema:
        return WorldSetupSchema(
            opening_scene="Scene",
            initial_problem="Problem",
            npcs=[{
                "name": "Iris",
                "description": "",
                "personality": "Calm",
                "resistance": 3,
                "relationship": 1,
            }],
        )

    def plan_turn(
        self,
        state: GameState,
        player_message: str,
    ) -> TurnResolutionSchema:
        self.turn_calls.append(player_message)
        return TurnResolutionSchema(
            active_npc={
                "name": "Iris",
                "description": "",
                "personality": "Calm",
                "resistance": 3,
                "relationship": 1,
            },
            npc_response="Sentence one. Sentence two. Sentence three.",
            outcome_type="Success",
            outcome_summary="You succeed.",
            npc_resistance_change=-1,
            npc_relationship_change=1,
            next_problem="Next problem",
            branches=[
                BranchSchema(title="A", description=""),
                BranchSchema(title="B", description=""),
                BranchSchema(title="C", description=""),
            ],
        )


def test_play_turn_updates_state_and_returns_record() -> None:
    fake_gpt = FakeGPTClient()
    mock_view = MagicMock()
    controller = GameController(fake_gpt, mock_view)
    state = controller._setup_world("Setting")

    result = controller._play_turn("message")
    record = result["record"]
    npc = result["npc"]

    assert record.outcome_type == "Success"
    assert npc.resistance == 2
    assert state.current_problem == "Next problem"
    assert fake_gpt.turn_calls[-1] == "message"


def test_retry_last_turn_uses_context() -> None:
    fake_gpt = FakeGPTClient()
    mock_view = MagicMock()
    controller = GameController(fake_gpt, mock_view)
    controller._setup_world("Setting")

    controller.retry_message = "retry message"
    result = controller._retry_last_turn()
    assert result["record"].player_message == "retry message"
    assert fake_gpt.turn_calls[-1] == "retry message"
    assert controller.retry_message is None
