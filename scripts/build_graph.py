from collections import defaultdict
import pickle


def load_words():
    with open(
        "data/processed/words_5.txt",
        "r"
    ) as f:

        return [
            line.strip().lower()
            for line in f
        ]


def build_graph(words):

    patterns = defaultdict(list)

    for word in words:

        for i in range(5):

            pattern = (
                word[:i]
                + "*"
                + word[i + 1:]
            )

            patterns[pattern].append(word)

    graph = defaultdict(set)

    for matching_words in patterns.values():

        for word in matching_words:

            for neighbor in matching_words:

                if word != neighbor:

                    graph[word].add(neighbor)

    return graph


def main():

    print("Loading words...")

    words = load_words()

    print(
        f"Loaded {len(words)} words"
    )

    print("Building graph...")

    graph = build_graph(words)

    print(
        f"Graph contains {len(graph)} nodes"
    )

    output_path = (
        "data/processed/graph.pkl"
    )

    with open(
        output_path,
        "wb"
    ) as f:

        pickle.dump(
            graph,
            f
        )

    print(
        f"Graph saved to {output_path}"
    )


if __name__ == "__main__":
    main()