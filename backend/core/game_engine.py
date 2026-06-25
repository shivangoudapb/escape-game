class EscapeGame:

    def __init__(
        self,
        start_word,
        graph
    ):

        self.start_word = start_word
        self.current_word = start_word

        self.graph = graph

        self.moves = 0

        self.history = [start_word]

    def validate_move(
        self,
        next_word
    ):
        """
        Returns:
        (True, None)

        or

        (False, error_message)
        """

        next_word = next_word.lower()

        if next_word == self.current_word:

            return (
                False,
                "You are already on that word."
            )

        if next_word not in self.graph:

            return (
                False,
                "Word not found in dictionary."
            )

        if next_word not in self.graph[self.current_word]:

            return (
                False,
                "Must change exactly one letter."
            )

        return (
            True,
            None
        )

    def make_move(
        self,
        next_word
    ):

        valid, message = self.validate_move(
            next_word
        )

        if not valid:

            return (
                False,
                message
            )

        self.current_word = next_word.lower()

        self.moves += 1

        self.history.append(
            self.current_word
        )

        return (
            True,
            None
        )

    def retained_letters(self):

        retained = 0

        for i in range(5):

            if (
                self.start_word[i]
                ==
                self.current_word[i]
            ):
                retained += 1

        return retained

    def escaped(self):

        return (
            self.retained_letters()
            == 0
        )

    def position_status(self):
        """
        Returns a list where:

        True  = retained (orange)
        False = escaped (black)
        """

        status = []

        for i in range(5):

            status.append(
                self.start_word[i]
                ==
                self.current_word[i]
            )

        return status

    def status_display(self):
        """
        Converts position status into symbols.
        """

        symbols = []

        for retained in self.position_status():

            if retained:
                symbols.append("🟧")
            else:
                symbols.append("⬛")

        return " ".join(symbols)

    def get_state(self):

        return {

            "start_word":
                self.start_word,

            "current_word":
                self.current_word,

            "moves":
                self.moves,

            "escaped":
                self.escaped(),

            "position_status":
                self.position_status(),

            "history":
                self.history
        }

    def summary(self):

        return {
            "start_word":
                self.start_word,

            "current_word":
                self.current_word,

            "moves":
                self.moves,

            "retained_letters":
                self.retained_letters(),

            "escaped":
                self.escaped(),

            "history":
                self.history
        }
    
    def undo(self):
        """
        Undo the last move.

        Returns:
        (True, None)

        or

        (False, error_message)
        """

        if len(self.history) <= 1:

            return (
                False,
                "Nothing to undo."
            )

        self.history.pop()

        self.current_word = (
            self.history[-1]
        )

        self.moves -= 1

        return (
            True,
            None
        )