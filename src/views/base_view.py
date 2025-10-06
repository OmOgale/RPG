from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from src.models.game_state import GameState, NPCState, TurnRecord


class BaseView(ABC):
    """Abstract view contract so different UIs can plug into the controller."""

    @abstractmethod
    def welcome(self) -> None:
        ...

    @abstractmethod
    def prompt_setting(self) -> Optional[str]:
        ...

    @abstractmethod
    def show_opening(self, opening_scene: str, initial_problem: str) -> None:
        ...

    @abstractmethod
    def start_turn(self, state: GameState) -> None:
        ...

    @abstractmethod
    def prompt_player_message(self) -> Tuple[Optional[str], bool]:
        ...

    @abstractmethod
    def handle_command(self, command: str, state: GameState) -> Tuple[bool, Optional[str]]:
        ...

    @abstractmethod
    def notify_empty_message(self) -> None:
        ...

    @abstractmethod
    def display_turn_resolution(self, record: TurnRecord, npc: NPCState) -> None:
        ...

    @abstractmethod
    def display_game_over(self, ending: str) -> None:
        ...

    @abstractmethod
    def notify_retry_available(self) -> None:
        ...

    @abstractmethod
    def display_error(self, message: str) -> None:
        ...

    @abstractmethod
    def say_goodbye(self) -> None:
        ...
