const GAME_KEY = "escape_current_game";

function todayKey() {
  // YYYY-MM-DD in local time
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export function saveCurrentGame(gameState) {
  const payload = {
    date: todayKey(),
    state: gameState,
  };
  localStorage.setItem(GAME_KEY, JSON.stringify(payload));
}

export function loadCurrentGame() {
  const raw = localStorage.getItem(GAME_KEY);
  if (!raw) return null;
  const payload = JSON.parse(raw);
  // Only valid if it's from today
  if (payload.date !== todayKey()) {
    localStorage.removeItem(GAME_KEY);
    return null;
  }
  return payload.state;
}

export function clearCurrentGame() {
  localStorage.removeItem(GAME_KEY);
}

export function hasTodayBeenPlayed() {
  const state = loadCurrentGame();
  return state !== null && state.escaped === true;
}
