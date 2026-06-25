import csv
import sys
from pathlib import Path

# Allow imports from backend/
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root / "backend"))

from graph import load_graph
from solver import optimal_moves


def main():

    print("Loading graph...")

    graph = load_graph()

    print(
        f"Loaded graph with "
        f"{len(graph)} words"
    )

    results = []

    total = len(graph)

    for index, word in enumerate(graph.keys(), start=1):

        if index % 100 == 0:

            print(
                f"Processed "
                f"{index}/{total}"
            )

        neighbors = len(
            graph[word]
        )

        moves = optimal_moves(
            word,
            graph
        )

        results.append(
            {
                "word": word,
                "neighbors": neighbors,
                "optimal_moves": moves
            }
        )

    output_file = (
        project_root
        / "data"
        / "processed"
        / "word_analysis.csv"
    )

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "word",
                "neighbors",
                "optimal_moves"
            ]
        )

        writer.writeheader()

        writer.writerows(
            results
        )

    print()

    print(
        f"Analysis saved to:"
    )

    print(output_file)

    print()

    print(
        f"Total words analyzed: "
        f"{len(results)}"
    )


if __name__ == "__main__":
    main()