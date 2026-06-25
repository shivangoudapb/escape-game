import pandas as pd


def main():

    df = pd.read_csv(
        "data/processed/reachability_analysis.csv"
    )

    print("\n========================")
    print("R1 STATISTICS")
    print("========================\n")

    print(
        df["r1"].describe()
    )

    print("\n========================")
    print("R2 STATISTICS")
    print("========================\n")

    print(
        df["r2"].describe()
    )

    print("\n========================")
    print("R3 STATISTICS")
    print("========================\n")

    print(
        df["r3"].describe()
    )

    print("\n========================")
    print("R4 STATISTICS")
    print("========================\n")

    print(
        df["r4"].describe()
    )

    print("\n========================")
    print("TOP 25 R4 WORDS")
    print("========================\n")

    print(
        df.sort_values(
            "r4",
            ascending=False
        )
        .head(25)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()