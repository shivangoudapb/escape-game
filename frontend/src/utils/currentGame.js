const GAME_KEY = "escape_current_game";

export function saveCurrentGame(gameState) {
  localStorage.setItem(
    GAME_KEY,
    JSON.stringify({
      game_id: gameState.game_id,
      puzzle_date: gameState.puzzle_date,
    }),
  );
}

export function getSavedGameId() {
  const raw = localStorage.getItem(GAME_KEY);
  if (!raw) return null;

  try {
    const payload = JSON.parse(raw);
    const isUuid = typeof payload.game_id === "string"
      && /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(payload.game_id);
    if (isUuid) return payload.game_id;
    localStorage.removeItem(GAME_KEY);
    return null;
  } catch {
    localStorage.removeItem(GAME_KEY);
    return null;
  }
}

export function clearCurrentGame() {
  localStorage.removeItem(GAME_KEY);
}
