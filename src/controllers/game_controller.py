from __future__ import annotations

from typing import Dict, Optional

from src.models.game_state import GameState
from src.models.schemas import TurnResolutionSchema, WorldSetupSchema
from src.services.gpt_client import GPTClient
from src.services.journal import JournalExporter
from src.views.base_view import BaseView
from src.views.cli_view import _QUIT_COMMANDS


class GameController:
    """Orchestrates the game loop using MVC Controller responsibilities."""

    def __init__(self, gpt_client: GPTClient, view: BaseView) -> None:
        self.gpt_client = gpt_client
        self.view = view
        self.state: Optional[GameState] = None
        self.journal = JournalExporter()
        self.retry_message: Optional[str] = None

    def run(self) -> None:
        self.view.welcome()
        setting = self.view.prompt_setting()
        if not setting or setting in _QUIT_COMMANDS:
            self.view.say_goodbye()
            return

        try:
            state = self._setup_world(setting)
        except Exception as exc:
            self.view.display_error(f"Failed to initialise the game: {exc}")
            return

        self.view.show_opening(state.opening_scene, state.current_problem)

        while True:
            self.view.start_turn(state)
            if self.retry_message:
                self.view.notify_retry_available()

            player_message, exit_requested = self.view.prompt_player_message()
            if exit_requested:
                self.view.say_goodbye()
                break
            if player_message is None or player_message == "":
                self.view.notify_empty_message()
                continue

            handled, response = self.view.handle_command(player_message, state)
            if handled:
                if response == "quit":
                    self.view.say_goodbye()
                    break
                if response == "log":
                    self._export_journal()
                    continue
                if response == "retry":
                    if not self.retry_message:
                        self.view.display_error("No turn available to retry.")
                        continue
                    try:
                        turn_result = self._retry_last_turn()
                    except Exception as exc:  # pragma: no cover - runtime guard
                        self.view.display_error(f"Retry failed: {exc}")
                        continue

                    record = turn_result["record"]
                    npc = turn_result["npc"]
                    self.view.display_turn_resolution(record, npc)

                    if turn_result["is_game_over"]:
                        ending = turn_result.get("ending_summary") or "The story concludes here."
                        self.view.display_game_over(ending)
                        break
                    continue
                continue

            self.retry_message = None
            try:
                turn_result = self._play_turn(player_message)
            except Exception as exc:  # pragma: no cover - runtime guard
                self.view.display_error(f"Encounter failed due to an error: {exc}")
                self.retry_message = player_message
                continue

            record = turn_result["record"]
            npc = turn_result["npc"]
            self.view.display_turn_resolution(record, npc)

            if turn_result["is_game_over"]:
                ending = turn_result.get("ending_summary") or "The story concludes here."
                self.view.display_game_over(ending)
                break

    def _setup_world(self, setting: str) -> GameState:
        schema: WorldSetupSchema = self.gpt_client.generate_world(setting)
        self.state = GameState.from_world_schema(setting, schema)
        return self.state

    def _play_turn(
        self,
        player_message: str,
    ) -> Dict[str, object]:
        if not self.state:
            raise RuntimeError("Game state is not initialized. Call _setup_world first.")

        resolution: TurnResolutionSchema = self.gpt_client.plan_turn(
            self.state, player_message
        )
        record, npc = self.state.apply_resolution(
            resolution, player_message
        )

        is_game_over = bool(resolution.is_game_over)
        ending_summary = resolution.ending_summary

        return {
            "record": record,
            "npc": npc,
            "next_problem": self.state.current_problem,
            "is_game_over": is_game_over,
            "ending_summary": ending_summary,
        }

    def state_snapshot(self) -> GameState:
        if not self.state:
            raise RuntimeError("Game state is not initialized. Call _setup_world first.")
        return self.state

    def _export_journal(self) -> None:
        if not self.state:
            return
        path = self.journal.export(self.state)
        self.view.display_error(f"Journal saved to {path}")

    def _retry_last_turn(self) -> Dict[str, object]:
        assert self.retry_message is not None
        player_message = self.retry_message
        result = self._play_turn(player_message)
        self.retry_message = None
        return result
