from pathlib import Path

raw = Path("data/raw/enable1.txt")
processed = Path("data/processed/words_5.txt")

with open(raw) as f:
    words = [
        line.strip().lower()
        for line in f
    ]

words = [
    w
    for w in words
    if len(w) == 5 and w.isalpha()
]

words = sorted(set(words))

with open(processed, "w") as f:
    f.write("\n".join(words))

print("Saved", len(words))