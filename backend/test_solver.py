from graph import load_graph

from solver import (
    shortest_escape,
    optimal_moves,
    can_escape
)


def main():

    graph = load_graph()

    start_word = input(
        "Start word: "
    ).strip().lower()

    print()

    print(
        "Checking..."
    )

    print()

    if not can_escape(
        start_word,
        graph
    ):

        print(
            "No escape found."
        )

        return

    path = shortest_escape(
        start_word,
        graph
    )

    print(
        "Shortest path:"
    )

    print()

    for word in path:

        print(word)

    print()

    print(
        f"Optimal moves: "
        f"{optimal_moves(start_word, graph)}"
    )


if __name__ == "__main__":
    main()