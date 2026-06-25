from fastapi import FastAPI
from pydantic import BaseModel

from backend.core.graph import load_graph
from backend.core.game_engine import EscapeGame
from backend.core.daily_selector import get_daily_word
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)

graph = load_graph()


class MoveRequest(BaseModel):

    current_word: str

    next_word: str

    start_word: str

    moves: int

    history: list[str]


@app.get("/")
def root():

    return {
        "message":
        "Escape API Running"
    }


@app.get("/daily-word")
def daily_word():

    return {
        "word":
        get_daily_word()
    }

@app.post("/new-game")
def new_game():

    start_word = get_daily_word()

    game = EscapeGame(
        start_word,
        graph
    )

    return game.get_state()

@app.post("/move")
def move(
    request: MoveRequest
):

    game = EscapeGame(
        request.start_word,
        graph
    )

    game.current_word = (
        request.current_word
    )

    game.moves = (
        request.moves
    )

    game.history = (
        request.history
    )

    success, message = (
        game.make_move(
            request.next_word
        )
    )

    return {

        "success":
            success,

        "message":
            message,

        "state":
            game.get_state()
    }