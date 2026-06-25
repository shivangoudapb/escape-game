import random
import pandas as pd

from datetime import (
    date,
    datetime,
    timezone
)


# Change this ONCE when the game launches.
LAUNCH_DATE = date(
    2026,
    6,
    17
)

# Fixed seed so the shuffle order
# is always identical everywhere.
SHUFFLE_SEED = 42


def load_candidates():

    df = pd.read_csv(
        "data/processed/candidate_words.csv"
    )

    return (
        df["word"]
        .tolist()
    )


def get_shuffled_words():

    words = load_candidates()

    rng = random.Random(
        SHUFFLE_SEED
    )

    rng.shuffle(
        words
    )

    return words


def get_utc_date():

    return (
        datetime.now(
            timezone.utc
        ).date()
    )


def get_day_number():

    today = get_utc_date()

    return (
        today
        -
        LAUNCH_DATE
    ).days


def get_daily_word():

    words = (
        get_shuffled_words()
    )

    day_number = (
        get_day_number()
    )

    if day_number < 0:

        raise ValueError(
            "Launch date is in the future."
        )

    index = (
        day_number
        %
        len(words)
    )

    return words[index]


def main():

    words = (
        get_shuffled_words()
    )

    utc_today = (
        get_utc_date()
    )

    day_number = (
        get_day_number()
    )

    word = (
        get_daily_word()
    )

    print()

    print(
        "===================="
    )

    print(
        "DAILY PUZZLE INFO"
    )

    print(
        "===================="
    )

    print()

    print(
        f"Launch Date   : "
        f"{LAUNCH_DATE}"
    )

    print(
        f"UTC Today     : "
        f"{utc_today}"
    )

    print(
        f"Day Number    : "
        f"{day_number}"
    )

    print()

    print(
        f"Today's Word  : "
        f"{word.upper()}"
    )

    print()

    print(
        f"Candidate Pool: "
        f"{len(words)}"
    )

    print()


if __name__ == "__main__":
    main()