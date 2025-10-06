from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from src.models.game_state import GameState
from src.models.schemas import (
    TurnResolutionSchema,
    ValidationError,
    WorldSetupSchema,
)

load_dotenv()


class GPTClient:
    def __init__(self, model: str | None = None, temperature: float = 0.8) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is required to play.")
        self.client = OpenAI(api_key=api_key)
        self.model = model or os.getenv("RPG_MODEL", "gpt-4o-mini")
        self.temperature = temperature

    def generate_world(self, setting: str) -> WorldSetupSchema:
        messages = [
            {
                "role": "system",
                "content": (
                    "You create lively RPG worlds for a persuasion-based adventure. "
                    "Reply with strict JSON using the schema: {\"opening_scene\": str, "
                    "\"initial_problem\": str, \"npcs\": [ {\"name\": str, "
                    "\"description\": str, \"personality\": str, \"resistance\": int, "
                    "\"relationship\": int } ] }. Provide 3-4 NPCs. "
                    "Make the scene vivid but concise."
                ),
            },
            {
                "role": "user",
                "content": (
                    "World or setting provided by the player: "
                    f"{setting}\nCreate the starting scenario, conflict, and NPC roster."
                ),
            },
        ]
        content = self._complete(messages)
        payload = self._safe_json(content)
        try:
            return WorldSetupSchema.model_validate(payload)
        except ValidationError as exc:
            raise RuntimeError(f"Model returned invalid world payload: {exc}") from exc

    def plan_turn(
        self,
        state: GameState,
        player_message: str,
    ) -> TurnResolutionSchema:
        npc_summary = state.npc_summary()
        summary_text, recent_turns = state.narrative_context(recent_limit=3)
        last_npc, streak = state.consecutive_npc_streak()
        payload = {
            "world_setting": state.world_setting,
            "opening_scene": state.opening_scene,
            "current_problem": state.current_problem,
            "npc_summary": npc_summary,
            "recent_history": recent_turns,
            "history_summary": summary_text,
            "player_message": player_message,
            "available_branches": state.pending_branches,
            "last_active_npc": last_npc,
            "npc_streak": streak,
        }
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the game master for a persuasion-centric RPG. "
                    "Always respond with JSON following the schema: {"
                    "\"active_npc\": {\"name\": str, \"description\": str, \"personality\": str, "
                    "\"resistance\": int, \"relationship\": int}, "
                    "\"npc_response\": str, \"outcome_type\": str (one of Success, Failure, Alternative), "
                    "\"outcome_summary\": str, \"npc_resistance_change\": int, "
                    "\"npc_relationship_change\": int, \"next_problem\": str, "
                    "\"branches\": [ {\"title\": str, \"description\": str} x3 ], "
                    "\"is_game_over\": bool, \"ending_summary\": str or null }. "
                    "NPC responses must be 3-4 sentences. Resolve a meaningful chunk of the current "
                    "conflict each turn so the story advances noticeably. Escalate stakes or push "
                    "toward resolution rather than repeating minor beats. Branches should describe "
                    "distinct, consequential paths for what happens next. Rotate between NPCs when "
                    "possible; avoid reusing the same NPC for consecutive turns unless the story "
                    "demands it, and justify when you do. If the player repeats the same argument "
                    "without new information, call it out and either increase resistance or deliver "
                    "a failure unless the story provides a compelling reason to reward them."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Here is the full game context as JSON. You must honor and extend it:\n"
                    f"{json.dumps(payload, ensure_ascii=True)}\n"
                    "Decide how the NPC responds, resolve the turn outcome, and set up the next problem."
                ),
            },
        ]
        return self._request_with_constraints(messages)

    def _request_with_constraints(self, messages: List[Dict[str, str]]) -> TurnResolutionSchema:
        attempts = 3
        last_error: Optional[Exception] = None
        for attempt in range(attempts):
            try:
                content = self._complete(messages)
                payload = self._safe_json(content)
                schema = TurnResolutionSchema.model_validate(payload)
                self._enforce_constraints(schema)
                return schema
            except (RuntimeError, ValidationError) as exc:
                last_error = exc
                if attempt < attempts - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise RuntimeError(f"Model response failed validation: {exc}") from exc
        assert last_error is not None  # pragma: no cover - defensive
        raise RuntimeError(f"Model response failed validation: {last_error}")

    def _complete(self, messages: List[Dict[str, str]]) -> str:
        delay = 1.0
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_completion_tokens=900,
                    timeout=30,
                )
                return response.choices[0].message.content.strip()
            except Exception as exc:
                if attempt == 2:
                    raise RuntimeError(f"GPT request failed: {exc}") from exc
                time.sleep(delay)
                delay *= 2

    @staticmethod
    def _safe_json(content: str) -> Dict[str, Any]:
        cleaned = GPTClient._strip_code_fences(content.strip())
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            extracted = GPTClient._extract_first_json(cleaned)
            if extracted:
                return json.loads(extracted)
            raise RuntimeError("Model returned invalid JSON and no recoverable payload")

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        if text.startswith("```") and text.endswith("```"):
            lines = text.splitlines()
            if lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            return "\n".join(lines).strip()
        return text

    @staticmethod
    def _extract_first_json(text: str) -> Optional[str]:
        depth = 0
        start_idx = None
        for idx, char in enumerate(text):
            if char == "{":
                if depth == 0:
                    start_idx = idx
                depth += 1
            elif char == "}":
                if depth:
                    depth -= 1
                    if depth == 0 and start_idx is not None:
                        candidate = text[start_idx : idx + 1]
                        try:
                            json.loads(candidate)
                            return candidate
                        except json.JSONDecodeError:
                            continue
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return match.group(0)
        return None

    @staticmethod
    def _enforce_constraints(resolution: TurnResolutionSchema) -> None:
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", resolution.npc_response.strip()) if s]
        if len(sentences) > 4:
            resolution.npc_response = " ".join(sentences[:4])
        if len(sentences) < 3:
            raise RuntimeError("NPC response too short; expected 3-4 sentences")

        unique_branches = []
        seen_titles = set()
        for branch in resolution.branches:
            title = branch.title.strip()
            if title.lower() in seen_titles:
                continue
            unique_branches.append(branch)
            seen_titles.add(title.lower())
            if len(unique_branches) == 3:
                break
        if not unique_branches:
            raise RuntimeError("No viable branches returned by model")
        resolution.branches = unique_branches
