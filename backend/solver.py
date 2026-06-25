from collections import deque


def retained_positions(
    start_word,
    current_word
):
    """
    Counts how many positions still match
    the original word.
    """

    retained = 0

    for i in range(5):

        if (
            start_word[i]
            ==
            current_word[i]
        ):
            retained += 1

    return retained


def escaped(
    start_word,
    current_word
):
    """
    Returns True if the word has escaped.
    """

    return (
        retained_positions(
            start_word,
            current_word
        )
        == 0
    )


def shortest_escape(
    start_word,
    graph
):
    """
    Uses BFS to find the shortest
    escape path.

    Returns:

    [
        word1,
        word2,
        ...
    ]

    or

    None
    """

    queue = deque()

    queue.append(
        (
            start_word,
            [start_word]
        )
    )

    visited = {
        start_word
    }

    while queue:

        current_word, path = (
            queue.popleft()
        )

        if escaped(
            start_word,
            current_word
        ):
            return path

        for neighbor in graph[
            current_word
        ]:

            if neighbor not in visited:

                visited.add(
                    neighbor
                )

                queue.append(
                    (
                        neighbor,
                        path + [neighbor]
                    )
                )

    return None


def can_escape(
    start_word,
    graph
):

    path = shortest_escape(
        start_word,
        graph
    )

    return path is not None


def optimal_moves(
    start_word,
    graph
):
    """
    Returns shortest move count.

    Example:

    path length = 6

    moves = 5
    """

    path = shortest_escape(
        start_word,
        graph
    )

    if path is None:
        return None

    return (
        len(path)
        - 1
    )