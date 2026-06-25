import pickle
import pandas as pd


def main():

    print("Loading graph...")

    with open(
        "data/processed/graph.pkl",
        "rb"
    ) as f:

        graph = pickle.load(f)

    results = []

    total = len(graph)

    for index, word in enumerate(graph, start=1):

        if index % 500 == 0:

            print(
                f"Processed {index}/{total}"
            )

        position_counts = [
            0, 0, 0, 0, 0
        ]

        for neighbor in graph[word]:

            for i in range(5):

                if (
                    word[i]
                    !=
                    neighbor[i]
                ):

                    position_counts[i] += 1

                    break

        diversity_score = (
            min(position_counts)
            if sum(position_counts) > 0
            else 0
        )

        results.append(
            {
                "word": word,
                "neighbors": len(graph[word]),

                "pos1":
                    position_counts[0],

                "pos2":
                    position_counts[1],

                "pos3":
                    position_counts[2],

                "pos4":
                    position_counts[3],

                "pos5":
                    position_counts[4],

                "diversity_score":
                    diversity_score
            }
        )

    df = pd.DataFrame(
        results
    )

    output_file = (
        "data/processed/"
        "word_diversity.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print()

    print(
        f"Saved to {output_file}"
    )

    print()

    print(
        "Top 30 diversity words:"
    )

    print(
        df.sort_values(
            "diversity_score",
            ascending=False
        )
        .head(30)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()