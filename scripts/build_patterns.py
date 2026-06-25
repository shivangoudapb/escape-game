from collections import defaultdict
from pathlib import Path

# Load words
words_file = Path("data/processed/words_5.txt")

with open(words_file, "r") as f:
    words = [line.strip().lower() for line in f]

print(f"Loaded {len(words)} words")

# Pattern -> words mapping
patterns = defaultdict(list)

for word in words:

    for i in range(len(word)):

        pattern = word[:i] + "*" + word[i + 1:]

        patterns[pattern].append(word)

print(f"Generated {len(patterns)} unique patterns")

# Test examples
test_patterns = [
    "s*one",
    "*tone",
    "ston*",
]

print("\n--- Sample Patterns ---")

for pattern in test_patterns:

    if pattern in patterns:

        print(f"\n{pattern}")
        print(patterns[pattern])

    else:
        print(f"\n{pattern}")
        print("Pattern not found")