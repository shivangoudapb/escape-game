from core.graph import load_graph
from core.game_engine import EscapeGame

import sys
from pathlib import Path

project_root = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

sys.path.append(
    str(project_root / "scripts")
)

from core.daily_selector import (
    get_daily_word
)


def render_status(
    game
):

    state = game.get_state()

    symbols = []

    for retained in state[
        "position_status"
    ]:

        if retained:

            symbols.append(
                "🟧"
            )

        else:

            symbols.append(
                "⬛"
            )

    print()

    print(
        "Original:",
        " ".join(
            game.start_word.upper()
        )
    )

    print(
        "Current :",
        " ".join(
            game.current_word.upper()
        )
    )

    print(
        "Status  :",
        " ".join(symbols)
    )

    print(
        "Moves   :",
        game.moves
    )

    print()


def main():

    print(
        "Loading graph..."
    )

    graph = load_graph()

    start_word = (
        get_daily_word()
    )

    game = EscapeGame(
        start_word,
        graph
    )

    print()

    print(
        "=== ESCAPE ==="
    )

    print()

    print(
        f"Starting word:"
        f" {start_word.upper()}"
    )

    while True:

        render_status(
            game
        )

        next_word = input(
            "Next word: "
        ).strip().lower()

        success, message = (
            game.make_move(
                next_word
            )
        )

        if not success:

            print()

            print(message)

            continue

        if game.escaped():

            print()

            print(
                "=" * 30
            )

            print()

            print(
                "ESCAPED!"
            )

            print()

            print(
                f"Start Word : "
                f"{game.start_word.upper()}"
            )

            print(
                f"Final Word : "
                f"{game.current_word.upper()}"
            )

            print(
                f"Moves      : "
                f"{game.moves}"
            )

            print()

            print(
                "=" * 30
            )

            break


if __name__ == "__main__":
    main()