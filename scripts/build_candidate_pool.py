import pickle
import pandas as pd

from wordfreq import zipf_frequency


MIN_R4 = 500

MIN_ZIPF = 3


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

    candidates = []

    total = len(reach_df)

    for index, row in enumerate(
        reach_df.itertuples(),
        start=1
    ):

        if index % 500 == 0:

            print(
                f"Processed "
                f"{index}/{total}"
            )

        word = row.word

        if word not in graph:
            continue

        frequency = zipf_frequency(
            word,
            "en"
        )

        if (
            row.r4 >= MIN_R4
            and
            frequency >= MIN_ZIPF
        ):

            candidates.append(
                {
                    "word": word,
                    "r4": row.r4,
                    "frequency": frequency,
                    "neighbors": len(
                        graph[word]
                    )
                }
            )

    candidate_df = pd.DataFrame(
        candidates
    )

    candidate_df = (
        candidate_df
        .sort_values(
            [
                "frequency",
                "r4"
            ],
            ascending=False
        )
    )

    output_file = (
        "data/processed/"
        "candidate_words.csv"
    )

    candidate_df.to_csv(
        output_file,
        index=False
    )

    print()

    print(
        f"Candidates found: "
        f"{len(candidate_df)}"
    )

    print()

    print(
        candidate_df
        .head(100)
        .to_string(index=False)
    )

    print()

    print(
        f"Saved to:"
    )

    print(
        output_file
    )


if __name__ == "__main__":
    main()