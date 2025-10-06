from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from src.models.schemas import NPCSchema, TurnResolutionSchema, WorldSetupSchema


@dataclass
class NPCState:
    name: str
    description: str
    personality: str
    resistance: int
    relationship: int

    def adjust(self, resistance_delta: int, relationship_delta: int) -> None:
        self.resistance = max(0, self.resistance + resistance_delta)
        self.relationship += relationship_delta

    @classmethod
    def from_schema(cls, schema: NPCSchema) -> NPCState:
        return cls(
            name=schema.name,
            description=schema.description,
            personality=schema.personality,
            resistance=schema.resistance,
            relationship=schema.relationship,
        )


@dataclass
class TurnRecord:
    turn_number: int
    npc_name: str
    dilemma: str
    player_message: str
    npc_response: str
    outcome_type: str
    outcome_summary: str
    resistance_shift: int
    relationship_shift: int
    branches: List[Dict[str, str]]


@dataclass
class GameState:
    world_setting: str
    opening_scene: str
    current_problem: str
    npcs: Dict[str, NPCState]
    turn_history: List[TurnRecord] = field(default_factory=list)
    total_successes: int = 0
    total_failures: int = 0
    pending_branches: List[Dict[str, str]] = field(default_factory=list)

    def record_turn(
        self,
        npc_name: str,
        dilemma: str,
        player_message: str,
        npc_response: str,
        outcome_type: str,
        outcome_summary: str,
        resistance_shift: int,
        relationship_shift: int,
        branches: List[Dict[str, str]],
    ) -> TurnRecord:
        record = TurnRecord(
            turn_number=len(self.turn_history) + 1,
            npc_name=npc_name,
            dilemma=dilemma,
            player_message=player_message,
            npc_response=npc_response,
            outcome_type=outcome_type,
            outcome_summary=outcome_summary,
            resistance_shift=resistance_shift,
            relationship_shift=relationship_shift,
            branches=branches,
        )
        self.turn_history.append(record)
        if outcome_type.lower() == "success":
            self.total_successes += 1
        elif outcome_type.lower() == "failure":
            self.total_failures += 1
        self.pending_branches = branches
        return record

    def npc_summary(self) -> List[Dict[str, str]]:
        summary = []
        for npc in self.npcs.values():
            summary.append(
                {
                    "name": npc.name,
                    "personality": npc.personality,
                    "resistance": str(npc.resistance),
                    "relationship": str(npc.relationship),
                }
            )
        return summary

    def recent_history(self, limit: int = 5) -> List[Dict[str, str]]:
        history = []
        for record in self.turn_history[-limit:]:
            history.append(
                {
                    "turn": record.turn_number,
                    "npc": record.npc_name,
                    "dilemma": record.dilemma,
                    "player_message": record.player_message,
                    "npc_response": record.npc_response,
                    "outcome": record.outcome_type,
                    "outcome_summary": record.outcome_summary,
                    "resistance_shift": record.resistance_shift,
                    "relationship_shift": record.relationship_shift,
                    "branches": record.branches,
                }
            )
        return history

    def  narrative_context(self, recent_limit: int = 3) -> Tuple[str, List[Dict[str, str]]]:
        recent = self.recent_history(limit=recent_limit)
        older = self.turn_history[:-recent_limit] if recent_limit else self.turn_history
        if not older:
            summary = ""
        else:
            snippets = []
            for record in older:
                snippets.append(
                    f"Turn {record.turn_number}: {record.npc_name} -> {record.outcome_type}; "
                    f"{record.outcome_summary[:80]}"
                )
            summary = " | ".join(snippets)
        return summary, recent

    def update_npc(self, npc_name: str, resistance_delta: int, relationship_delta: int) -> None:
        npc = self.npcs.get(npc_name)
        if npc:
            npc.adjust(resistance_delta, relationship_delta)

    def ensure_npc(self, npc_payload: Dict[str, str]) -> NPCState:
        npc_name = npc_payload["name"]
        npc = self.npcs.get(npc_name)
        if not npc:
            npc = NPCState(
                name=npc_payload["name"],
                description=npc_payload.get("description", ""),
                personality=npc_payload.get("personality", ""),
                resistance=int(npc_payload.get("resistance", 5)),
                relationship=int(npc_payload.get("relationship", 0)),
            )
            self.npcs[npc_name] = npc
        return npc

    @classmethod
    def from_world_schema(cls, setting: str, schema: WorldSetupSchema) -> GameState:
        npcs = {npc_schema.name: NPCState.from_schema(npc_schema) for npc_schema in schema.npcs}
        return cls(
            world_setting=setting,
            opening_scene=schema.opening_scene,
            current_problem=schema.initial_problem,
            npcs=npcs,
        )

    def apply_resolution(
        self,
        resolution: TurnResolutionSchema,
        player_message: str,
    ) -> tuple[TurnRecord, NPCState]:
        npc_payload = resolution.active_npc.model_dump()
        npc = self.ensure_npc(npc_payload)

        prev_resistance = npc.resistance
        prev_relationship = npc.relationship

        resistance_delta, relationship_delta = self._normalize_deltas(
            resolution.normalised_outcome(),
            resolution.npc_resistance_change,
            resolution.npc_relationship_change,
        )
        npc.adjust(resistance_delta, relationship_delta)

        actual_resistance_shift = npc.resistance - prev_resistance
        actual_relationship_shift = npc.relationship - prev_relationship

        branches = [branch.model_dump() for branch in resolution.branches[:3]]
        record = self.record_turn(
            npc_name=npc.name,
            dilemma=self.current_problem,
            player_message=player_message,
            npc_response=resolution.npc_response,
            outcome_type=resolution.normalised_outcome(),
            outcome_summary=resolution.outcome_summary,
            resistance_shift=actual_resistance_shift,
            relationship_shift=actual_relationship_shift,
            branches=branches,
        )

        self.current_problem = resolution.next_problem or self.current_problem
        self.pending_branches = branches
        return record, npc

    def last_active_npc(self) -> Optional[str]:
        if not self.turn_history:
            return None
        return self.turn_history[-1].npc_name

    def consecutive_npc_streak(self) -> Tuple[Optional[str], int]:
        if not self.turn_history:
            return (None, 0)
        last_name = self.turn_history[-1].npc_name
        count = 0
        for record in reversed(self.turn_history):
            if record.npc_name == last_name:
                count += 1
            else:
                break
        return (last_name, count)

    @staticmethod
    def _normalize_deltas(
        outcome: str,
        resistance_change: int,
        relationship_change: int,
    ) -> tuple[int, int]:
        outcome_key = outcome.strip().lower()
        if outcome_key == "success":
            resistance_change = min(resistance_change, -1)
            relationship_change = max(relationship_change, 1)
        elif outcome_key == "failure":
            resistance_change = max(resistance_change, 0)
            relationship_change = min(relationship_change, 0)
        else:  # Alternative or anything else
            resistance_change = max(min(resistance_change, 2), -2)
            relationship_change = max(min(relationship_change, 2), -2)

        return resistance_change, relationship_change
