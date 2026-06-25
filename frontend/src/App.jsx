import { useEffect, useState } from "react";
import "./App.css";
import { recordWin, getStats } from "./utils/stats";
import { saveCurrentGame, loadCurrentGame, hasTodayBeenPlayed } from "./utils/currentGame";

function App() {
  const [game, setGame] = useState(null);
  const [inputWord, setInputWord] = useState("");
  const [message, setMessage] = useState("");
  const [shake, setShake] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [showStats, setShowStats] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [darkMode, setDarkMode] = useState(true);
  const [stats, setStats] = useState(getStats());
  const [copied, setCopied] = useState(false);
  const [alreadyPlayed, setAlreadyPlayed] = useState(false);

  useEffect(() => {
    if (darkMode) {
      document.body.classList.remove("light-mode");
    } else {
      document.body.classList.add("light-mode");
    }
  }, [darkMode]);

  useEffect(() => {
    // Check for a saved game from today first
    const saved = loadCurrentGame();

    if (saved) {
      // Resume exactly where they left off (mid-game or completed)
      setGame(saved);
      if (saved.escaped) {
        // Already completed today — show stats immediately
        setAlreadyPlayed(true);
        setShowStats(true);
      }
      return;
    }

    // No saved game for today — fetch a fresh one
    fetch("http://127.0.0.1:8000/new-game", { method: "POST" })
      .then(response => response.json())
      .then(data => {
        setGame(data);
        saveCurrentGame(data);
      });
  }, []);

  function triggerError(text) {
    setInputWord("");
    setMessage(text);
    setShake(true);
    setTimeout(() => setShake(false), 500);
    setTimeout(() => setMessage(""), 2000);
  }

  async function submitMove() {
    if (!game || game.escaped) return;
    if (inputWord.length !== 5) {
      triggerError("Word must be 5 letters.");
      return;
    }

    const response = await fetch("http://127.0.0.1:8000/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        start_word: game.start_word,
        current_word: game.current_word,
        moves: game.moves,
        history: game.history,
        next_word: inputWord.toLowerCase(),
      }),
    });

    const data = await response.json();

    if (!data.success) {
      triggerError(data.message);
      return;
    }

    const newState = data.state;
    setGame(newState);
    saveCurrentGame(newState);

    if (newState.escaped) {
      recordWin(newState.moves);
      setStats(getStats());
      setTimeout(() => setShowStats(true), 800);
    }

    setInputWord("");
  }

  useEffect(() => {
    function handleKeyPress(event) {
      if (!game || game.escaped) return;
      const key = event.key;

      if (/^[a-zA-Z]$/.test(key)) {
        setInputWord(current =>
          current.length < 5 ? current + key.toLowerCase() : current
        );
      } else if (key === "Backspace") {
        setInputWord(current => current.slice(0, -1));
      } else if (key === "Enter") {
        submitMove();
      }
    }

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [game, inputWord]);

  function handleShare() {
    if (!game) return;
    const moves = game.moves;
    const extra = moves - 5;
    const extraText = extra === 0 ? "perfect!" : `+${extra} extra`;
    const text = `ESCAPE\n${game.start_word.toUpperCase()} → escaped in ${moves} moves (${extraText})\nBest possible: 5 moves\n${window.location.href}`;
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  if (!game) return <h2>Loading...</h2>;

  const maxCount = Math.max(1, ...Object.values(stats.distribution));

  return (
    <div className="container">
      <div className="game-area">

        <div className="title-bar">
          <h1>ESCAPE</h1>
          <p className="title-tagline">escape the word</p>
        </div>

        <div className="message">{message}</div>

        <div className="board">
          {game.history.map((word, rowIndex) => (
            <div key={rowIndex} className="tile-row">
              {word
                .toUpperCase()
                .split("")
                .map((letter, letterIndex) => (
                  <div
                    key={letterIndex}
                    className={
                      rowIndex === 0
                        ? "tile start-tile"
                        : word[letterIndex] === game.start_word[letterIndex]
                        ? "tile retained-tile"
                        : "tile escaped-tile"
                    }
                  >
                    {letter}
                  </div>
                ))}
            </div>
          ))}

          {!game.escaped && (
            <div className={shake ? "tile-row shake" : "tile-row"}>
              {Array.from({ length: 5 }).map((_, index) => (
                <div key={index} className="tile input-tile">
                  {inputWord[index]?.toUpperCase()}
                </div>
              ))}
            </div>
          )}
        </div>

        {game.escaped && <h2 className="escaped-message">ESCAPED!</h2>}
      </div>

      <div className="bottom-section">
        <div className="keyboard">
          <div className="keyboard-row">
            {"QWERTYUIOP".split("").map(letter => (
              <button
                key={letter}
                className="key"
                onClick={() => {
                  if (game.escaped || inputWord.length >= 5) return;
                  setInputWord(current => current + letter.toLowerCase());
                }}
              >
                {letter}
              </button>
            ))}
          </div>

          <div className="keyboard-row">
            {"ASDFGHJKL".split("").map(letter => (
              <button
                key={letter}
                className="key"
                onClick={() => {
                  if (game.escaped || inputWord.length >= 5) return;
                  setInputWord(current => current + letter.toLowerCase());
                }}
              >
                {letter}
              </button>
            ))}
          </div>

          <div className="keyboard-row">
            <button className="key wide-key" onClick={submitMove}>
              ENTER
            </button>

            {"ZXCVBNM".split("").map(letter => (
              <button
                key={letter}
                className="key"
                onClick={() => {
                  if (game.escaped || inputWord.length >= 5) return;
                  setInputWord(current => current + letter.toLowerCase());
                }}
              >
                {letter}
              </button>
            ))}

            <button
              className="key wide-key"
              onClick={() => setInputWord(current => current.slice(0, -1))}
            >
              ⌫
            </button>
          </div>
        </div>

        <div className="footer-buttons">
          <button className="footer-button" onClick={() => setShowHelp(true)}>
            How To Play
          </button>
          <button className="footer-button" onClick={() => setShowStats(true)}>
            Stats
          </button>
          <button className="footer-button" onClick={() => setShowSettings(true)}>
            Settings
          </button>
        </div>
      </div>

      {/* HOW TO PLAY MODAL */}
      {showHelp && (
        <div className="modal-overlay">
          <div className="modal">
            <button className="close-button" onClick={() => setShowHelp(false)}>✕</button>
            <h2 className="help-title">HOW TO PLAY</h2>
            <p className="hero-text">ESCAPE ALL FIVE LETTERS.</p>
            <p className="help-text">Each move must change exactly one letter.</p>
            <p className="example-label">Example</p>
            <div className="help-example">
              <div className="help-row">
                {["S","T","O","C","K"].map(l => (
                  <div key={l} className="help-tile orange">{l}</div>
                ))}
              </div>
              <div className="help-row">
                <div className="help-tile orange">S</div>
                <div className="help-tile orange">T</div>
                <div className="help-tile grey">A</div>
                <div className="help-tile orange">C</div>
                <div className="help-tile orange">K</div>
              </div>
            </div>
            <p className="escape-explanation">The <strong>O</strong> escaped.</p>
            <p className="goal-text">Keep changing one letter at a time until every position has escaped.</p>
          </div>
        </div>
      )}

      {/* STATS MODAL */}
      {showStats && (
        <div className="modal-overlay">
          <div className="modal modal-stats">
            <button className="close-button" onClick={() => setShowStats(false)}>✕</button>

            {game.escaped && (
              <div className="win-banner">
                {alreadyPlayed && (
                  <p className="already-played-note">You already escaped today's word.</p>
                )}
                <p className="win-congrats">You escaped!</p>
                <p className="win-detail">
                  You used <span className="win-accent">{game.moves}</span> guess{game.moves !== 1 ? "es" : ""}
                </p>
                <p className="win-best">Best possible solution was <span className="win-accent">5</span> guesses</p>
                <button className="share-button" onClick={handleShare}>
                  {copied ? "Copied!" : "Copy Result"}
                </button>
                <div className="win-divider" />
              </div>
            )}

            <h2 className="help-title">STATS</h2>

            <div className="stats-grid">
              <div className="stat">
                <div className="stat-value">{stats.gamesPlayed}</div>
                <div className="stat-label">Games</div>
              </div>
              <div className="stat">
                <div className="stat-value">{stats.wins}</div>
                <div className="stat-label">Wins</div>
              </div>
              <div className="stat">
                <div className="stat-value">
                  {stats.gamesPlayed === 0
                    ? "—"
                    : (stats.totalExtraMoves / stats.gamesPlayed).toFixed(2)}
                </div>
                <div className="stat-label">Avg. Extra</div>
              </div>
              <div className="stat">
                <div className="stat-value">{stats.currentStreak}</div>
                <div className="stat-label">Streak</div>
              </div>
              <div className="stat">
                <div className="stat-value">{stats.bestStreak}</div>
                <div className="stat-label">Best Streak</div>
              </div>
              <div className="stat">
                <div className="stat-value">{stats.bestGame ?? "—"}</div>
                <div className="stat-label">Best Game</div>
              </div>
            </div>

            <p className="distribution-title">Distribution</p>

            <div className="distribution">
              {Object.entries(stats.distribution).map(([extraMoves, count]) => (
                <div key={extraMoves} className="distribution-row">
                  <div className="distribution-label">{extraMoves}</div>
                  <div className="distribution-bar-container">
                    <div
                      className="distribution-bar"
                      style={{ width: `${Math.max(4, (count / maxCount) * 100)}%` }}
                    >
                      {count > 0 && <span>{count}</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>

          </div>
        </div>
      )}

      {/* SETTINGS MODAL */}
      {showSettings && (
        <div className="modal-overlay">
          <div className="modal">
            <button className="close-button" onClick={() => setShowSettings(false)}>✕</button>
            <h2 className="help-title">SETTINGS</h2>
            <div className="settings-row">
              <span className="settings-label">Dark Mode</span>
              <button
                className={`toggle ${darkMode ? "toggle-on" : "toggle-off"}`}
                onClick={() => setDarkMode(prev => !prev)}
                aria-label="Toggle dark mode"
              >
                <span className="toggle-knob" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;