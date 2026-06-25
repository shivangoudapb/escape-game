import pandas as pd


def main():

    df = pd.read_csv(
        "data/processed/word_analysis.csv"
    )

    print("\n========================")
    print("DATASET OVERVIEW")
    print("========================\n")

    print(
        f"Total words: {len(df)}"
    )

    print()

    print(
        "Neighbor Statistics"
    )

    print(
        df["neighbors"].describe()
    )

    print()

    print(
        "Optimal Move Statistics"
    )

    print(
        df["optimal_moves"].describe()
    )

    print()

    print(
        "Neighbor Distribution"
    )

    bins = [
        0,
        2,
        5,
        10,
        15,
        20,
        30,
        100
    ]

    labels = [
        "1-2",
        "3-5",
        "6-10",
        "11-15",
        "16-20",
        "21-30",
        "30+"
    ]

    df["neighbor_bucket"] = pd.cut(
        df["neighbors"],
        bins=bins,
        labels=labels
    )

    print(
        df["neighbor_bucket"]
        .value_counts()
        .sort_index()
    )

    print()

    print(
        "Optimal Move Distribution"
    )

    print(
        df["optimal_moves"]
        .value_counts()
        .sort_index()
    )

    print()

    print(
        "Top 25 Most Connected Words"
    )

    print(
        df.sort_values(
            "neighbors",
            ascending=False
        )
        .head(25)
        .to_string(index=False)
    )

    print()

    print(
        "Bottom 25 Least Connected Words"
    )

    print(
        df.sort_values(
            "neighbors",
            ascending=True
        )
        .head(25)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()