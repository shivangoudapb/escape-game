from collections import defaultdict, deque


def load_words():
    with open("data/processed/words_5.txt", "r") as f:
        return [line.strip().lower() for line in f]


def build_graph(words):
    """
    Builds the one-letter-change graph.

    Example:

    stone -> shone
    stone -> stoke
    stone -> atone

    because they differ by exactly one letter.
    """

    patterns = defaultdict(list)

    for word in words:
        for i in range(5):
            pattern = word[:i] + "*" + word[i + 1:]
            patterns[pattern].append(word)

    graph = defaultdict(set)

    for matching_words in patterns.values():

        for word in matching_words:

            for neighbor in matching_words:

                if word != neighbor:
                    graph[word].add(neighbor)

    return graph


def escaped(start_word, current_word):
    """
    Returns True if no letter remains
    in its original position.
    """

    for i in range(5):

        if start_word[i] == current_word[i]:
            return False

    return True


def find_shortest_escape(start_word, graph):
    """
    BFS search.

    Returns the shortest escape path.
    """

    queue = deque()

    queue.append((start_word, [start_word]))

    visited = set()
    visited.add(start_word)

    while queue:

        current_word, path = queue.popleft()

        # Have we escaped?
        if escaped(start_word, current_word):
            return path

        for neighbor in graph[current_word]:

            if neighbor not in visited:

                visited.add(neighbor)

                queue.append(
                    (
                        neighbor,
                        path + [neighbor]
                    )
                )

    return None


def main():

    words = load_words()

    print(f"Loaded {len(words)} words")

    print("Building graph...")

    graph = build_graph(words)

    print(f"Graph contains {len(graph)} nodes")

    start_word = input(
        "\nEnter a starting word: "
    ).strip().lower()

    if start_word not in graph:

        print("Word not found in dictionary.")
        return

    print("\nSearching...\n")

    path = find_shortest_escape(
        start_word,
        graph
    )

    if path is None:

        print("No escape path found.")
        return

    print("Escape found!\n")

    for word in path:
        print(word)

    print(
        f"\nMoves required: {len(path) - 1}"
    )


if __name__ == "__main__":
    main()