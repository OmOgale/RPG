from __future__ import annotations

from src.controllers.game_controller import GameController
from src.services.gpt_client import GPTClient
from src.views.cli_view import CLIView


def main() -> None:
    client = GPTClient()
    view = CLIView()
    controller = GameController(client, view)
    controller.run()


if __name__ == "__main__":
    main()
