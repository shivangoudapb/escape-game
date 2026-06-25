const STORAGE_KEY = "escape_stats";
const WIN_DATE_KEY = "escape_last_win_date";

const DEFAULT_STATS = {
  gamesPlayed: 0,
  wins: 0,
  totalExtraMoves: 0,
  currentStreak: 0,
  bestStreak: 0,
  bestGame: null,
  distribution: {
    0: 0,
    1: 0,
    2: 0,
    3: 0,
    4: 0,
    5: 0,
    "6+": 0,
  },
};

function todayKey() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export function getStats() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (!saved) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_STATS));
    return { ...DEFAULT_STATS };
  }
  return JSON.parse(saved);
}

export function saveStats(stats) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(stats));
}

export function hasWonToday() {
  return localStorage.getItem(WIN_DATE_KEY) === todayKey();
}

export function recordWin(moves) {
  // Guard: never record the same day twice
  if (hasWonToday()) return;
  localStorage.setItem(WIN_DATE_KEY, todayKey());

  const stats = getStats();
  const extraMoves = Math.max(0, moves - 5);

  stats.gamesPlayed += 1;
  stats.wins += 1;
  stats.totalExtraMoves += extraMoves;
  stats.currentStreak += 1;
  stats.bestStreak = Math.max(stats.bestStreak, stats.currentStreak);

  if (stats.bestGame === null || moves < stats.bestGame) {
    stats.bestGame = moves;
  }

  if (extraMoves >= 6) {
    stats.distribution["6+"] += 1;
  } else {
    stats.distribution[extraMoves] += 1;
  }

  saveStats(stats);
}

export function resetStats() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_STATS));
  localStorage.removeItem(WIN_DATE_KEY);
}