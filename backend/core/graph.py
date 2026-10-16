import pickle
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_graph():

    with (PROJECT_ROOT / "data" / "processed" / "graph.pkl").open("rb") as f:

        return pickle.load(f)
