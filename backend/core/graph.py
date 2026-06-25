import pickle


def load_graph():

    with open(
        "data/processed/graph.pkl",
        "rb"
    ) as f:

        return pickle.load(f)