"""SQLite persistence for anonymous game sessions and completed results."""

import json
import os
import hashlib
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def database_path():
    configured_path = os.getenv("ESCAPE_DATABASE_PATH")
    if configured_path:
        return Path(configured_path).expanduser().resolve()
    if os.getenv("RENDER", "").lower() == "true":
        # Render's free filesystem is writable but ephemeral across restarts/deploys.
        return Path("/tmp/escape.sqlite3")
    return PROJECT_ROOT / "backend" / "escape.sqlite3"


def connect():
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def database_connection():
    connection = connect()
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database():
    with database_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                google_sub TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL,
                display_name TEXT,
                picture_url TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS players (
                id TEXT PRIMARY KEY,
                user_id TEXT UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS auth_sessions (
                token_hash TEXT PRIMARY KEY,
                player_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_auth_sessions_player_id
                ON auth_sessions (player_id);

            CREATE TABLE IF NOT EXISTS games (
                id TEXT PRIMARY KEY,
                puzzle_date TEXT NOT NULL,
                start_word TEXT NOT NULL,
                current_word TEXT NOT NULL,
                moves INTEGER NOT NULL DEFAULT 0,
                history_json TEXT NOT NULL,
                escaped INTEGER NOT NULL DEFAULT 0,
                player_id TEXT REFERENCES players(id),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_games_puzzle_date
                ON games (puzzle_date);

            CREATE TABLE IF NOT EXISTS completed_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL UNIQUE REFERENCES games(id),
                puzzle_date TEXT NOT NULL,
                start_word TEXT NOT NULL,
                final_word TEXT NOT NULL,
                moves INTEGER NOT NULL,
                completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_results_puzzle_date
                ON completed_results (puzzle_date);
            """
        )
        game_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(games)").fetchall()
        }
        if "player_id" not in game_columns:
            connection.execute(
                "ALTER TABLE games ADD COLUMN player_id TEXT REFERENCES players(id)"
            )


def _state_from_row(row):
    return {
        "game_id": row["id"],
        "puzzle_date": row["puzzle_date"],
        "start_word": row["start_word"],
        "current_word": row["current_word"],
        "moves": row["moves"],
        "history": json.loads(row["history_json"]),
        "escaped": bool(row["escaped"]),
        "player_id": row["player_id"],
    }


def get_game(game_id: UUID | str):
    with database_connection() as connection:
        row = connection.execute(
            "SELECT * FROM games WHERE id = ?",
            (str(game_id),),
        ).fetchone()
    return _state_from_row(row) if row else None


def create_game(game_id: UUID, puzzle_date: str, start_word: str, player_id: str):
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO games (id, puzzle_date, start_word, current_word, history_json, player_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(game_id),
                puzzle_date,
                start_word,
                start_word,
                json.dumps([start_word]),
                player_id,
            ),
        )
    return get_game(game_id)


def _token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _session_info(row):
    user = None
    if row["user_id"]:
        user = {
            "email": row["email"],
            "display_name": row["display_name"],
            "picture_url": row["picture_url"],
        }
    return {
        "player_id": row["player_id"],
        "authenticated": user is not None,
        "user": user,
    }


def get_session(token):
    if not token:
        return None
    now = datetime.now(timezone.utc).isoformat()
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT p.id AS player_id, p.user_id, u.email, u.display_name, u.picture_url
            FROM auth_sessions s
            JOIN players p ON p.id = s.player_id
            LEFT JOIN users u ON u.id = p.user_id
            WHERE s.token_hash = ? AND s.expires_at > ?
            """,
            (_token_hash(token), now),
        ).fetchone()
    return _session_info(row) if row else None


def _create_player_session(connection, player_id, lifetime):
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + lifetime).isoformat()
    connection.execute(
        "INSERT INTO auth_sessions (token_hash, player_id, expires_at) VALUES (?, ?, ?)",
        (_token_hash(token), player_id, expires_at),
    )
    return token


def create_anonymous_session():
    player_id = str(uuid4())
    with database_connection() as connection:
        connection.execute("INSERT INTO players (id) VALUES (?)", (player_id,))
        token = _create_player_session(connection, player_id, timedelta(days=365))
        row = connection.execute(
            "SELECT id AS player_id, user_id, NULL AS email, NULL AS display_name, NULL AS picture_url FROM players WHERE id = ?",
            (player_id,),
        ).fetchone()
    return token, _session_info(row)


def ensure_session(token):
    purge_expired_sessions()
    session = get_session(token)
    if session:
        return token, session, False
    token, session = create_anonymous_session()
    return token, session, True


def purge_expired_sessions():
    """Remove expired credentials and the anonymous game data tied to them."""
    now = datetime.now(timezone.utc).isoformat()
    with database_connection() as connection:
        connection.execute("DELETE FROM auth_sessions WHERE expires_at <= ?", (now,))
        expired_guest_players = """
            SELECT p.id FROM players p
            WHERE p.user_id IS NULL
              AND NOT EXISTS (
                  SELECT 1 FROM auth_sessions s WHERE s.player_id = p.id
              )
        """
        connection.execute(
            f"DELETE FROM completed_results WHERE game_id IN "
            f"(SELECT id FROM games WHERE player_id IN ({expired_guest_players}))"
        )
        connection.execute(
            f"DELETE FROM games WHERE player_id IN ({expired_guest_players})"
        )
        connection.execute(
            f"DELETE FROM players WHERE id IN ({expired_guest_players})"
        )


def authenticate_google_user(google_sub, email, display_name, picture_url, current_token=None):
    """Create or find a Google account and claim the current anonymous player's games."""
    token_hash = _token_hash(current_token) if current_token else None
    new_token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)

    with database_connection() as connection:
        current_session = None
        if token_hash:
            current_session = connection.execute(
                """
                SELECT s.token_hash, p.id AS player_id, p.user_id
                FROM auth_sessions s JOIN players p ON p.id = s.player_id
                WHERE s.token_hash = ? AND s.expires_at > ?
                """,
                (token_hash, now.isoformat()),
            ).fetchone()

        user = connection.execute(
            "SELECT id FROM users WHERE google_sub = ?",
            (google_sub,),
        ).fetchone()
        if user:
            user_id = user["id"]
            connection.execute(
                """
                UPDATE users SET email = ?, display_name = ?, picture_url = ?,
                    updated_at = CURRENT_TIMESTAMP WHERE id = ?
                """,
                (email, display_name, picture_url, user_id),
            )
        else:
            user_id = str(uuid4())
            connection.execute(
                """
                INSERT INTO users (id, google_sub, email, display_name, picture_url)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, google_sub, email, display_name, picture_url),
            )

        player = connection.execute(
            "SELECT id FROM players WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if player:
            player_id = player["id"]
        else:
            player_id = str(uuid4())
            connection.execute(
                "INSERT INTO players (id, user_id) VALUES (?, ?)",
                (player_id, user_id),
            )

        if current_session:
            if current_session["user_id"] is None:
                connection.execute(
                    "UPDATE games SET player_id = ? WHERE player_id = ?",
                    (player_id, current_session["player_id"]),
                )
                connection.execute(
                    "DELETE FROM auth_sessions WHERE token_hash = ?",
                    (current_session["token_hash"],),
                )
                connection.execute(
                    "DELETE FROM players WHERE id = ? AND user_id IS NULL",
                    (current_session["player_id"],),
                )

        connection.execute(
            "INSERT INTO auth_sessions (token_hash, player_id, expires_at) VALUES (?, ?, ?)",
            (_token_hash(new_token), player_id, (now + timedelta(days=30)).isoformat()),
        )
        row = connection.execute(
            """
            SELECT p.id AS player_id, p.user_id, u.email, u.display_name, u.picture_url
            FROM players p JOIN users u ON u.id = p.user_id WHERE p.id = ?
            """,
            (player_id,),
        ).fetchone()

    return new_token, _session_info(row)


def claim_unowned_game(game_id, player_id):
    with database_connection() as connection:
        cursor = connection.execute(
            "UPDATE games SET player_id = ? WHERE id = ? AND player_id IS NULL",
            (player_id, str(game_id)),
        )
    return cursor.rowcount == 1


def get_player_stats(player_id, today):
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT r.puzzle_date, MIN(r.moves) AS moves
            FROM completed_results r
            JOIN games g ON g.id = r.game_id
            WHERE g.player_id = ?
            GROUP BY r.puzzle_date
            ORDER BY r.puzzle_date DESC
            """,
            (player_id,),
        ).fetchall()

    distribution = {**{str(i): 0 for i in range(6)}, "6+": 0}
    best_game = None
    total_extra_moves = 0
    for row in rows:
        extra_moves = max(0, row["moves"] - 5)
        total_extra_moves += extra_moves
        key = str(extra_moves) if extra_moves < 6 else "6+"
        distribution[key] += 1
        best_game = row["moves"] if best_game is None else min(best_game, row["moves"])

    solved_dates = {row["puzzle_date"] for row in rows}
    today_date = date.fromisoformat(today)
    most_recent = today_date if today in solved_dates else today_date - timedelta(days=1)
    current_streak = 0
    while most_recent.isoformat() in solved_dates:
        current_streak += 1
        most_recent -= timedelta(days=1)

    best_streak = 0
    running_streak = 0
    previous = None
    for solved_date in sorted(date.fromisoformat(value) for value in solved_dates):
        running_streak = (
            running_streak + 1
            if previous and (solved_date - previous).days == 1
            else 1
        )
        best_streak = max(best_streak, running_streak)
        previous = solved_date

    games_played = len(rows)
    return {
        "gamesPlayed": games_played,
        "wins": games_played,
        "totalExtraMoves": total_extra_moves,
        "currentStreak": current_streak,
        "bestStreak": best_streak,
        "bestGame": best_game,
        "distribution": distribution,
    }


def logout_session(token):
    if token:
        with database_connection() as connection:
            connection.execute(
                "DELETE FROM auth_sessions WHERE token_hash = ?",
                (_token_hash(token),),
            )


def delete_account(token):
    session = get_session(token)
    if not session or not session["authenticated"]:
        return False

    with database_connection() as connection:
        connection.execute(
            "DELETE FROM completed_results WHERE game_id IN (SELECT id FROM games WHERE player_id = ?)",
            (session["player_id"],),
        )
        connection.execute("DELETE FROM games WHERE player_id = ?", (session["player_id"],))
        connection.execute(
            "DELETE FROM users WHERE id = (SELECT user_id FROM players WHERE id = ?)",
            (session["player_id"],),
        )
    return True


def save_game_state(game_id, previous_moves, previous_word, state):
    """Save a move and its result atomically; reject stale concurrent updates."""
    with database_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.execute(
            """
            UPDATE games
            SET current_word = ?, moves = ?, history_json = ?, escaped = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND moves = ? AND current_word = ? AND escaped = 0
            """,
            (
                state["current_word"],
                state["moves"],
                json.dumps(state["history"]),
                int(state["escaped"]),
                str(game_id),
                previous_moves,
                previous_word,
            ),
        )
        if cursor.rowcount != 1:
            return False

        if state["escaped"]:
            connection.execute(
                """
                INSERT INTO completed_results
                    (game_id, puzzle_date, start_word, final_word, moves)
                SELECT id, puzzle_date, start_word, current_word, moves
                FROM games WHERE id = ?
                """,
                (str(game_id),),
            )
        return True
