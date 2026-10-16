import os
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from fastapi import FastAPI, Header, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from fastapi.middleware.cors import CORSMiddleware

from backend.core.daily_selector import get_daily_puzzle, get_utc_date
from backend.core.game_engine import EscapeGame
from backend.core.graph import load_graph
from backend.core.persistence import (
    create_game,
    create_anonymous_session,
    connect,
    database_path,
    delete_account as delete_account_data,
    ensure_session,
    authenticate_google_user,
    claim_unowned_game,
    get_game,
    get_player_stats,
    get_session,
    initialize_database,
    logout_session,
    save_game_state,
)


app = FastAPI()

APP_ENV = os.getenv("APP_ENV", "development").lower()
IS_RENDER = os.getenv("RENDER", "").lower() == "true"
IS_PRODUCTION = APP_ENV == "production" or IS_RENDER
CORS_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "CORS_ORIGINS",
        "https://playescape.vercel.app" if IS_PRODUCTION else "http://localhost:5173",
    ).split(",")
    if origin.strip()
]

if IS_PRODUCTION:
    if not CORS_ORIGINS:
        raise RuntimeError("Set CORS_ORIGINS to the exact production frontend origin(s).")
    if not IS_RENDER and not os.getenv("ESCAPE_DATABASE_PATH"):
        raise RuntimeError("Set ESCAPE_DATABASE_PATH to a durable mounted database path.")
    configured_database_path = database_path()
    if not os.path.isabs(str(configured_database_path)):
        raise RuntimeError("ESCAPE_DATABASE_PATH must be an absolute path in production.")
    if IS_RENDER:
        has_persistent_mount = any(
            os.path.ismount(str(parent))
            for parent in (Path(configured_database_path).parent, *Path(configured_database_path).parent.parents)
            if str(parent) != os.path.abspath(os.sep)
        )
        if not has_persistent_mount:
            raise RuntimeError(
                "Attach a Render persistent disk and set ESCAPE_DATABASE_PATH inside its mount path."
            )
    for origin in CORS_ORIGINS:
        parsed_origin = urlsplit(origin)
        if (
            parsed_origin.scheme != "https"
            or not parsed_origin.netloc
            or parsed_origin.path
            or parsed_origin.query
            or parsed_origin.fragment
        ):
            raise RuntimeError("Production CORS_ORIGINS must contain HTTPS origins only, without paths.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-Escape-Request"],
)

graph = load_graph()
initialize_database()


class NewGameRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    game_id: UUID | None = None


class MoveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    game_id: UUID
    expected_moves: int = Field(ge=0, le=1000)
    expected_current_word: str = Field(pattern=r"^[a-z]{5}$")
    next_word: str = Field(pattern=r"^[a-z]{5}$")


class GoogleLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    credential: str = Field(min_length=20, max_length=8192)


def format_game_state(game_record):
    game = EscapeGame(game_record["start_word"], graph)
    game.current_word = game_record["current_word"]
    game.moves = game_record["moves"]
    game.history = game_record["history"]
    return {
        **game.get_state(),
        "game_id": game_record["game_id"],
        "puzzle_date": game_record["puzzle_date"],
    }


def set_session_cookie(response, token, authenticated=False):
    response.set_cookie(
        key="escape_session",
        value=token,
        max_age=30 * 24 * 60 * 60 if authenticated else 365 * 24 * 60 * 60,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        path="/",
    )


def require_request_marker(value):
    if value != "1":
        raise HTTPException(status_code=403, detail="Missing request verification header.")


@app.get("/")
def root():
    return {"message": "Escape API Running"}


@app.get("/health")
def health():
    try:
        connection = connect()
        try:
            connection.execute("SELECT 1")
        finally:
            connection.close()
    except Exception:
        raise HTTPException(status_code=503, detail="Database is unavailable.")
    return {"status": "ok"}


@app.get("/daily-word")
def daily_word():
    return get_daily_puzzle()


@app.post("/new-game")
def new_game(
    request: NewGameRequest,
    http_request: Request,
    response: Response,
    x_escape_request: str | None = Header(default=None),
):
    require_request_marker(x_escape_request)
    puzzle = get_daily_puzzle()
    token, player, created = ensure_session(http_request.cookies.get("escape_session"))
    if created:
        set_session_cookie(response, token)

    if request.game_id:
        existing_game = get_game(request.game_id)
        if existing_game and existing_game["puzzle_date"] == puzzle["puzzle_date"]:
            owned = existing_game["player_id"] == player["player_id"]
            if existing_game["player_id"] is None:
                owned = claim_unowned_game(request.game_id, player["player_id"])
                existing_game = get_game(request.game_id)
            if owned:
                return format_game_state(existing_game)

    game_record = create_game(
        uuid4(), puzzle["puzzle_date"], puzzle["word"], player["player_id"]
    )
    return format_game_state(game_record)


@app.post("/move")
def move(
    request: MoveRequest,
    http_request: Request,
    response: Response,
    x_escape_request: str | None = Header(default=None),
):
    require_request_marker(x_escape_request)
    puzzle = get_daily_puzzle()
    token, player, created = ensure_session(http_request.cookies.get("escape_session"))
    if created:
        set_session_cookie(response, token)
    game_record = get_game(request.game_id)

    if not game_record:
        raise HTTPException(status_code=404, detail="Game session not found. Start a new game.")
    if game_record["player_id"] is None:
        claim_unowned_game(request.game_id, player["player_id"])
        game_record = get_game(request.game_id)
    if game_record["player_id"] != player["player_id"]:
        raise HTTPException(status_code=404, detail="Game session not found. Start a new game.")
    if game_record["puzzle_date"] != puzzle["puzzle_date"]:
        raise HTTPException(status_code=409, detail="This puzzle has expired. Refresh to load today's puzzle.")
    if game_record["escaped"]:
        raise HTTPException(status_code=409, detail="This game is already complete.")
    if (
        request.expected_moves != game_record["moves"]
        or request.expected_current_word != game_record["current_word"]
    ):
        raise HTTPException(status_code=409, detail="Game state changed. Reload the current game and try again.")
    if game_record["moves"] >= 1000:
        raise HTTPException(status_code=409, detail="This game has reached its move limit.")

    game = EscapeGame(game_record["start_word"], graph)
    game.current_word = game_record["current_word"]
    game.moves = game_record["moves"]
    game.history = game_record["history"]

    success, message = game.make_move(request.next_word)
    if not success:
        return {
            "success": False,
            "message": message,
            "state": format_game_state(game_record),
        }

    if not save_game_state(
        request.game_id,
        game_record["moves"],
        game_record["current_word"],
        game.get_state(),
    ):
        raise HTTPException(
            status_code=409,
            detail="Game state changed. Reload the current game and try again.",
        )

    return {
        "success": True,
        "message": None,
        "state": format_game_state(get_game(request.game_id)),
    }


@app.get("/auth/me")
def auth_me(request: Request):
    session = get_session(request.cookies.get("escape_session"))
    if not session:
        return {"authenticated": False, "user": None}
    return {"authenticated": session["authenticated"], "user": session["user"]}


@app.post("/auth/google")
def google_login(
    request: GoogleLoginRequest,
    http_request: Request,
    response: Response,
    x_escape_request: str | None = Header(default=None),
):
    require_request_marker(x_escape_request)
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured yet.")

    try:
        from google.auth.transport.requests import Request as GoogleRequest
        from google.oauth2 import id_token

        claims = id_token.verify_oauth2_token(
            request.credential,
            GoogleRequest(),
            audience=client_id,
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Google credential is invalid or expired.")
    except Exception:
        raise HTTPException(status_code=503, detail="Google sign-in could not be verified. Try again.")

    email_verified = claims.get("email_verified")
    if not claims.get("sub") or not claims.get("email") or email_verified not in (True, "true"):
        raise HTTPException(status_code=401, detail="Google did not provide a verified email address.")

    token, session = authenticate_google_user(
        google_sub=claims["sub"],
        email=claims["email"],
        display_name=claims.get("name"),
        picture_url=claims.get("picture"),
        current_token=http_request.cookies.get("escape_session"),
    )
    set_session_cookie(response, token, authenticated=True)
    return {"authenticated": True, "user": session["user"]}


@app.get("/stats")
def player_stats(request: Request, response: Response):
    token, player, created = ensure_session(request.cookies.get("escape_session"))
    if created:
        set_session_cookie(response, token)
    return get_player_stats(player["player_id"], get_utc_date().isoformat())


@app.post("/auth/logout")
def logout(
    request: Request,
    response: Response,
    x_escape_request: str | None = Header(default=None),
):
    require_request_marker(x_escape_request)
    logout_session(request.cookies.get("escape_session"))
    token, _player = create_anonymous_session()
    set_session_cookie(response, token)
    return {"authenticated": False, "user": None}


@app.delete("/auth/account")
def delete_user_account(
    request: Request,
    response: Response,
    x_escape_request: str | None = Header(default=None),
):
    require_request_marker(x_escape_request)
    current_token = request.cookies.get("escape_session")
    if not delete_account_data(current_token):
        raise HTTPException(status_code=401, detail="Sign in to delete your account.")
    logout_session(current_token)
    token, _player = create_anonymous_session()
    set_session_cookie(response, token)
    return {"deleted": True}
