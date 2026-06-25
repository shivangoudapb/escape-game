import pickle
import pandas as pd
from collections import deque


def reachable_within_depth(
    start_word,
    graph,
    max_depth
):
    """
    Returns number of unique words reachable
    within max_depth moves.
    """

    visited = {start_word}

    queue = deque()

    queue.append(
        (
            start_word,
            0
        )
    )

    while queue:

        current_word, depth = (
            queue.popleft()
        )

        if depth == max_depth:
            continue

        for neighbor in graph[current_word]:

            if neighbor not in visited:

                visited.add(
                    neighbor
                )

                queue.append(
                    (
                        neighbor,
                        depth + 1
                    )
                )

    return len(visited) - 1


def main():

    print(
        "Loading graph..."
    )

    with open(
        "data/processed/graph.pkl",
        "rb"
    ) as f:

        graph = pickle.load(f)

    total_words = len(graph)

    print(
        f"Loaded {total_words} words"
    )

    results = []

    for index, word in enumerate(
        graph.keys(),
        start=1
    ):

        if index % 100 == 0:

            print(
                f"Processed "
                f"{index}/{total_words}"
            )

        r1 = reachable_within_depth(
            word,
            graph,
            1
        )

        r2 = reachable_within_depth(
            word,
            graph,
            2
        )

        r3 = reachable_within_depth(
            word,
            graph,
            3
        )

        r4 = reachable_within_depth(
            word,
            graph,
            4
        )

        results.append(
            {
                "word": word,
                "r1": r1,
                "r2": r2,
                "r3": r3,
                "r4": r4
            }
        )

    df = pd.DataFrame(
        results
    )

    output_file = (
        "data/processed/"
        "reachability_analysis.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print()

    print(
        f"Saved to:"
    )

    print(
        output_file
    )

    print()

    print(
        "Done."
    )


if __name__ == "__main__":
    main()