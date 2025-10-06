from __future__ import annotations

import textwrap
from typing import Dict, List, Optional, Tuple

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.models.game_state import GameState, NPCState, TurnRecord

from .base_view import BaseView

_QUIT_COMMANDS = {"quit"}
_LOG_COMMANDS = {"log"}
_RETRY_COMMANDS = {"retry"}


class CLIView(BaseView):
    """Console view implementation following the BaseView strategy."""

    def __init__(self, width: int = 80, console: Console | None = None) -> None:
        self.width = width
        self.console = console or Console()

    def welcome(self) -> None:
        self.console.print(
            Panel.fit(
                "Welcome to the adventure. Type 'quit' to exit at any time.",
                title="RPG",
                border_style="magenta",
            )
        )

    def prompt_setting(self) -> Optional[str]:
        setting = self.console.input("[bold cyan]Choose a world or setting to explore:[/]\n> ").strip()
        return setting or None

    def show_opening(self, opening_scene: str, initial_problem: str) -> None:
        self.console.print(
            Panel(
                self._wrap(opening_scene),
                title="Opening Scene",
                border_style="cyan",
                width=self.width + 4,
            )
        )
    def start_turn(self, state: GameState) -> None:
        self.console.print(
            Panel(
                self._wrap(state.current_problem),
                title="Current Dilemma",
                border_style="green",
                width=self.width + 4,
            )
        )

        roster = Table(title="NPC Roster", box=box.ROUNDED, expand=False)
        roster.add_column("Name", style="bold")
        roster.add_column("Resistance", justify="right")
        roster.add_column("Relationship", justify="right")
        roster.add_column("Personality")
        for npc in state.npcs.values():
            roster.add_row(
                npc.name,
                str(npc.resistance),
                str(npc.relationship),
                npc.personality or "--",
            )
        self.console.print(roster)

    def prompt_player_message(self) -> Tuple[Optional[str], bool]:
        player_message = self._prompt("\n[bold magenta]How do you persuade them?[/]\n> ")
        lowered = player_message.lower()
        if lowered in _QUIT_COMMANDS:
            return None, True
        return player_message, False

    def notify_empty_message(self) -> None:
        self.console.print("[bold red]You need to say something to progress.[/]")

    def display_turn_resolution(self, record: TurnRecord, npc: NPCState) -> None:
        res_shift = self._format_shift(record.resistance_shift)
        rel_shift = self._format_shift(record.relationship_shift)

        response_panel = Panel(
            self._wrap(record.npc_response),
            title=f"NPC Response ({record.npc_name})",
            border_style="blue",
            width=self.width + 4,
        )
        self.console.print(response_panel)

        summary_text = Text()
        summary_text.append(f"Outcome: {record.outcome_type}\n", style="bold")
        summary_text.append(self._wrap(record.outcome_summary) + "\n")
        summary_text.append(
            f"Resistance shift: {res_shift} (now {npc.resistance}) | "
            f"Relationship shift: {rel_shift} (now {npc.relationship})"
        )
        self.console.print(
            Panel(summary_text, border_style="purple", width=self.width + 4)
        )

        self._render_branches(record.branches, heading="Branches to Explore")

    def display_game_over(self, ending: str) -> None:
        self.console.print(
            Panel(
                self._wrap(ending),
                title="Ending",
                border_style="gold1",
                width=self.width + 4,
            )
        )
        self.console.print("[bold green]Thanks for adventuring![/]")

    def display_error(self, message: str) -> None:
        self.console.print(f"[bold red]{message}[/]")

    def say_goodbye(self) -> None:
        self.console.print("[bold]Thanks for playing![/]")

    def handle_command(self, command: str, state: GameState) -> Tuple[bool, Optional[str]]:
        lowered = command.lower()
        if lowered in _LOG_COMMANDS:
            return True, "log"
        if lowered in _QUIT_COMMANDS:
            return True, "quit"
        if lowered in _RETRY_COMMANDS:
            return True, "retry"
        return False, None

    def notify_retry_available(self) -> None:
        self.console.print(
            "[italic]You can type 'retry' to attempt the last persuasion again or provide a new message.[/]"
        )

    def _wrap(self, text: str) -> str:
        if not text:
            return ""
        return textwrap.fill(str(text), width=self.width)

    def _prompt(self, message: str) -> str:
        return self.console.input(message).strip()

    @staticmethod
    def _format_shift(value: int) -> str:
        sign = "+" if value > 0 else "" if value < 0 else "±"
        return f"{sign}{value}" if sign != "±" else "0"

    def _render_branches(self, branches: List[Dict[str, str]], heading: str = "Branches") -> None:
        table = Table(title=heading, box=box.SIMPLE, expand=False)
        table.add_column("#", justify="right", style="bold")
        table.add_column("Title", style="cyan")
        table.add_column("Description")
        for idx, branch in enumerate(branches, start=1):
            table.add_row(str(idx), branch.get("title", f"Option {idx}"), branch.get("description", ""))
        self.console.print(table)
