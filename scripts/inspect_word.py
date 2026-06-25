import pickle
import pandas as pd


def main():

    print("Loading graph...")

    with open(
        "data/processed/graph.pkl",
        "rb"
    ) as f:

        graph = pickle.load(f)

    print(
        "Loading reachability data..."
    )

    reach_df = pd.read_csv(
        "data/processed/reachability_analysis.csv"
    )

    reach_lookup = {}

    for _, row in reach_df.iterrows():

        reach_lookup[
            row["word"]
        ] = {
            "r1": row["r1"],
            "r2": row["r2"],
            "r3": row["r3"],
            "r4": row["r4"]
        }

    print()

    word = input(
        "Enter word: "
    ).strip().lower()

    if word not in graph:

        print(
            "\nWord not found."
        )

        return

    neighbors = sorted(
        graph[word]
    )

    print("\n====================")
    print("WORD ANALYSIS")
    print("====================\n")

    print(
        f"Word      : {word}"
    )

    print(
        f"Neighbors : {len(neighbors)}"
    )

    print(
        f"R2        : "
        f"{reach_lookup[word]['r2']}"
    )

    print(
        f"R3        : "
        f"{reach_lookup[word]['r3']}"
    )

    print(
        f"R4        : "
        f"{reach_lookup[word]['r4']}"
    )

    print()

    print("====================")
    print("NEIGHBORS")
    print("====================\n")

    rows = []

    for neighbor in neighbors:

        rows.append(
            (
                neighbor,
                reach_lookup[
                    neighbor
                ]["r4"]
            )
        )

    rows.sort(
        key=lambda x: x[1],
        reverse=True
    )

    for neighbor, r4 in rows:

        print(
            f"{neighbor:<10}"
            f"R4={r4}"
        )


if __name__ == "__main__":
    main()