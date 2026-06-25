import pandas as pd

from wordfreq import zipf_frequency


def main():

    reach_df = pd.read_csv(
        "data/processed/reachability_analysis.csv"
    )

    results = []

    total = len(reach_df)

    print(
        f"Processing {total} words..."
    )

    for index, row in enumerate(
        reach_df.itertuples(),
        start=1
    ):

        if index % 500 == 0:

            print(
                f"Processed "
                f"{index}/{total}"
            )

        frequency = zipf_frequency(
            row.word,
            "en"
        )

        results.append(
            {
                "word": row.word,
                "zipf": frequency,
                "r4": row.r4
            }
        )

    df = pd.DataFrame(
        results
    )

    output_file = (
        "data/processed/"
        "word_frequency.csv"
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
    print("=" * 40)
    print("ZIPF STATISTICS")
    print("=" * 40)
    print()

    print(
        df["zipf"].describe()
    )

    print()
    print("=" * 40)
    print("TOP 50 MOST COMMON")
    print("=" * 40)
    print()

    print(
        df.sort_values(
            "zipf",
            ascending=False
        )
        .head(50)
        .to_string(index=False)
    )

    print()
    print("=" * 40)
    print("BOTTOM 50 LEAST COMMON")
    print("=" * 40)
    print()

    print(
        df.sort_values(
            "zipf",
            ascending=True
        )
        .head(50)
        .to_string(index=False)
    )

    print()
    print("=" * 40)
    print("WORDS WE CARE ABOUT")
    print("=" * 40)
    print()

    test_words = [
        "start",
        "stack",
        "stone",
        "plant",
        "table",
        "heart",
        "grape",
        "roper",
        "tabid"
    ]

    for word in test_words:

        freq = zipf_frequency(
            word,
            "en"
        )

        print(
            f"{word:<10} {freq:.2f}"
        )


if __name__ == "__main__":
    main()