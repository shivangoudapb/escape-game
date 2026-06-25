import pandas as pd


def main():

    print("Loading reachability data...")

    df = pd.read_csv(
        "data/processed/reachability_analysis.csv"
    )

    print(
        f"Loaded {len(df)} words"
    )

    print()

    print("Current Statistics")
    print("-" * 30)

    print(
        f"Median R4 : "
        f"{df['r4'].median():.0f}"
    )

    print(
        f"75th percentile R4 : "
        f"{df['r4'].quantile(0.75):.0f}"
    )

    print(
        f"90th percentile R4 : "
        f"{df['r4'].quantile(0.90):.0f}"
    )

    print()

    min_r4 = int(
        input(
            "Minimum R4: "
        )
    )

    candidates = df[
        df["r4"] >= min_r4
    ].copy()

    candidates = (
        candidates
        .sort_values(
            "r4",
            ascending=False
        )
    )

    print()

    print(
        f"Found "
        f"{len(candidates)} "
        f"candidate words"
    )

    print()

    print(
        candidates.head(100)
        .to_string(index=False)
    )

    output_file = (
        "data/processed/"
        "candidate_words.csv"
    )

    candidates.to_csv(
        output_file,
        index=False
    )

    print()

    print(
        f"Saved to:"
    )

    print(output_file)


if __name__ == "__main__":
    main()