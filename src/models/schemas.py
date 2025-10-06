from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError


class NPCSchema(BaseModel):
    name: str
    description: str = ""
    personality: str = ""
    resistance: int = Field(default=5, ge=0)
    relationship: int = 0


class WorldSetupSchema(BaseModel):
    opening_scene: str
    initial_problem: str = Field(default="Convince someone to listen.")
    npcs: List[NPCSchema] = Field(default_factory=list)


class BranchSchema(BaseModel):
    title: str
    description: str = ""


class TurnResolutionSchema(BaseModel):
    active_npc: NPCSchema
    npc_response: str
    outcome_type: str
    outcome_summary: str
    npc_resistance_change: int = 0
    npc_relationship_change: int = 0
    next_problem: str
    branches: List[BranchSchema] = Field(default_factory=list)
    is_game_over: bool = False
    ending_summary: Optional[str] = None

    def normalised_outcome(self) -> str:
        outcome = self.outcome_type.strip().lower()
        if outcome in {"success", "failure", "alternative"}:
            return outcome.capitalize()
        return "Alternative"


__all__ = [
    "NPCSchema",
    "WorldSetupSchema",
    "BranchSchema",
    "TurnResolutionSchema",
    "ValidationError",
]
