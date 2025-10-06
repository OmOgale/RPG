from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from src.models.game_state import GameState, TurnRecord


class JournalExporter:
    """Saves the game history to disk (JSON)."""

    def __init__(self, output_dir: str = "journals") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, state: GameState) -> Path:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = self.output_dir / f"journal_{timestamp}.json"
        payload = self._state_to_payload(state)
        with filename.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        return filename

    @staticmethod
    def _state_to_payload(state: GameState) -> Dict[str, Any]:
        return {
            "world_setting": state.world_setting,
            "opening_scene": state.opening_scene,
            "current_problem": state.current_problem,
            "total_successes": state.total_successes,
            "total_failures": state.total_failures,
            "turns": [JournalExporter._record_to_dict(record) for record in state.turn_history],
            "npcs": {
                name: {
                    "description": npc.description,
                    "personality": npc.personality,
                    "resistance": npc.resistance,
                    "relationship": npc.relationship,
                }
                for name, npc in state.npcs.items()
            },
        }

    @staticmethod
    def _record_to_dict(record: TurnRecord) -> Dict[str, Any]:
        data = asdict(record)
        return data
