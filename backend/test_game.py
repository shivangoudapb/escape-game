from graph import (
    load_graph
)

from game_engine import (
    EscapeGame
)


def main():

    print(
        "Loading graph..."
    )

    graph = load_graph()

    print(
        f"Loaded graph with "
        f"{len(graph)} nodes"
    )

    start_word = input(
        "\nStart word: "
    ).strip().lower()

    if start_word not in graph:

        print(
            "Word not found."
        )

        return

    game = EscapeGame(
        start_word,
        graph
    )

    while True:

        print()

        print(
            "Original:",
            " ".join(game.start_word.upper())
        )

        print(
            "Current :",
            " ".join(game.current_word.upper())
        )

        print(
            "Status  :",
            game.status_display()
        )

        print(
            "Moves   :",
            game.moves
        )

        if game.escaped():

            print()

            print("═" * 30)

            print("\n🎉 ESCAPED! 🎉\n")

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
                f"Path:"
            )

            print(
                " → ".join(
                    word.upper()
                    for word in game.history
                )
            )

            print()

            print("═" * 30)

            break

        next_word = input(
            "\nNext word: "
        ).strip().lower()

        success, message = game.make_move(
            next_word
        )

        if not success:

            print(
                f"\n{message}"
            )

if __name__ == "__main__":
    main()