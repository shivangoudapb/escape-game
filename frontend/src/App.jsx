import { useCallback, useEffect, useState } from "react";
import "./App.css";
import { getStats } from "./utils/stats";
import { clearCurrentGame, saveCurrentGame, getSavedGameId } from "./utils/currentGame";

function getApiUrl() {
  if (import.meta.env.PROD) return "/api";

  const configuredUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const apiUrl = new URL(configuredUrl, window.location.origin);
  const isLoopbackHost = host => host === "localhost" || host === "127.0.0.1";

  // localhost and 127.0.0.1 are different cookie sites in browsers. Keep a local
  // API on the same loopback hostname as the page so its session cookie is sent.
  if (isLoopbackHost(apiUrl.hostname) && isLoopbackHost(window.location.hostname)) {
    apiUrl.hostname = window.location.hostname;
  }

  return `${apiUrl.origin}${apiUrl.pathname.replace(/\/$/, "")}`;
}

const API_URL = getApiUrl();
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "1073055591607-ps26ttfq2pum84t7hp7t91ovieqh7u0u.apps.googleusercontent.com";
let googleIdentityPromise;

function apiFetch(path, options = {}) {
  return fetch(`${API_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "X-Escape-Request": "1",
      ...options.headers,
    },
  });
}

function loadGoogleIdentity() {
  if (window.google?.accounts?.id) return Promise.resolve();
  if (googleIdentityPromise) return googleIdentityPromise;

  googleIdentityPromise = new Promise((resolve, reject) => {
    let script = document.getElementById("google-identity-services");
    const shouldAppend = !script;
    if (!script) {
      script = document.createElement("script");
      script.id = "google-identity-services";
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
    }
    script.addEventListener("load", () => {
      if (window.google?.accounts?.id) resolve();
      else {
        googleIdentityPromise = undefined;
        reject(new Error("Google Identity Services did not initialize."));
      }
    }, { once: true });
    script.addEventListener("error", () => {
      script.remove();
      googleIdentityPromise = undefined;
      reject(new Error("Google Identity Services failed to load."));
    }, { once: true });
    if (shouldAppend) document.head.appendChild(script);
  });
  return googleIdentityPromise;
}

function App() {
  const [game, setGame] = useState(null);
  const [inputWord, setInputWord] = useState("");
  const [message, setMessage] = useState("");
  const [shake, setShake] = useState(false);
  const [revealedMove, setRevealedMove] = useState(null);
  const [showHelp, setShowHelp] = useState(false);
  const [showStats, setShowStats] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [darkMode, setDarkMode] = useState(true);
  const [stats, setStats] = useState(getStats());
  const [copied, setCopied] = useState(false);
  const [alreadyPlayed, setAlreadyPlayed] = useState(false);
  const [showAccount, setShowAccount] = useState(false);
  const [account, setAccount] = useState(null);
  const [accountMessage, setAccountMessage] = useState("");

  useEffect(() => {
    if (darkMode) {
      document.body.classList.remove("light-mode");
    } else {
      document.body.classList.add("light-mode");
    }
  }, [darkMode]);

  useEffect(() => {
    apiFetch("/new-game", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_id: getSavedGameId() }),
    })
      .then(response => {
        if (!response.ok) throw new Error("Could not load today's puzzle.");
        return response.json();
      })
      .then(data => {
        setGame(data);
        saveCurrentGame(data);
        if (data.escaped) {
          setAlreadyPlayed(true);
          setShowStats(true);
        }
        return Promise.all([
          apiFetch("/auth/me").then(response => response.json()),
          apiFetch("/stats").then(response => response.json()),
        ]);
      })
      .then(([authData, statsData]) => {
        setAccount(authData.authenticated ? authData.user : null);
        setStats(statsData);
      })
      .catch(() => setMessage("Could not load today's puzzle. Please refresh to try again."));
  }, []);

  useEffect(() => {
    if (!showAccount || !GOOGLE_CLIENT_ID) return undefined;
    let active = true;

    loadGoogleIdentity()
      .then(() => {
        if (!active) return;
        const button = document.getElementById("google-sign-in-button");
        if (!button) return;
        button.replaceChildren();
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: async ({ credential }) => {
            setAccountMessage("Signing in...");
            try {
              const response = await apiFetch("/auth/google", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ credential }),
              });
              const data = await response.json();
              if (!response.ok) throw new Error(data.detail || "Google sign-in failed.");
              setAccount(data.user);
              setAccountMessage("Your progress is now linked to your Google account.");
              const statsResponse = await apiFetch("/stats");
              if (statsResponse.ok) setStats(await statsResponse.json());
            } catch (error) {
              setAccountMessage(error.message || "Google sign-in failed. Please try again.");
            }
          },
          auto_select: false,
        });
        window.google.accounts.id.renderButton(button, {
          theme: darkMode ? "filled_black" : "outline",
          size: "large",
          shape: "rectangular",
          text: "continue_with",
          width: 280,
        });
      })
      .catch(() => setAccountMessage("Google sign-in could not load. Check your connection and try again."));

    return () => { active = false; };
  }, [showAccount, darkMode]);

  const refreshStats = useCallback(async () => {
    const response = await apiFetch("/stats");
    if (response.ok) setStats(await response.json());
  }, []);

  async function startAnonymousGame() {
    clearCurrentGame();
    const response = await apiFetch("/new-game", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_id: null }),
    });
    if (!response.ok) throw new Error("Could not start an anonymous game.");
    const newGame = await response.json();
    setGame(newGame);
    saveCurrentGame(newGame);
    setAlreadyPlayed(false);
    await refreshStats();
  }

  async function signOut() {
    try {
      const response = await apiFetch("/auth/logout", { method: "POST" });
      if (!response.ok) throw new Error("Could not sign out.");
      setAccount(null);
      setAccountMessage("You are signed out. You can keep playing anonymously.");
      await startAnonymousGame();
    } catch (error) {
      setAccountMessage(error.message || "Could not sign out. Please try again.");
    }
  }

  async function deleteAccount() {
    const confirmed = window.confirm(
      "Delete your Google-linked account and all saved game results? This cannot be undone.",
    );
    if (!confirmed) return;
    try {
      const response = await apiFetch("/auth/account", { method: "DELETE" });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not delete the account.");
      setAccount(null);
      setAccountMessage("Your account and saved results were deleted. You can keep playing anonymously.");
      await startAnonymousGame();
    } catch (error) {
      setAccountMessage(error.message || "Could not delete the account. Please try again.");
    }
  }

  const triggerError = useCallback((text) => {
    setInputWord("");
    setMessage(text);
    setShake(true);
    setTimeout(() => setShake(false), 500);
    setTimeout(() => setMessage(""), 2000);
  }, []);

  const submitMove = useCallback(async () => {
    if (!game || game.escaped) return;
    if (inputWord.length !== 5) {
      triggerError("Word must be 5 letters.");
      return;
    }

    const response = await apiFetch("/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        game_id: game.game_id,
        expected_moves: game.moves,
        expected_current_word: game.current_word,
        next_word: inputWord.toLowerCase(),
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      triggerError(error.detail || "Could not submit move. Please try again.");
      return;
    }
    const data = await response.json();

    if (!data.success) {
      triggerError(data.message);
      return;
    }

    const newState = data.state;
    const changedLetterIndex = [...inputWord].findIndex(
      (letter, index) => letter !== game.current_word[index],
    );
    setRevealedMove({
      rowIndex: newState.history.length - 1,
      letterIndex: changedLetterIndex,
    });
    setGame(newState);
    saveCurrentGame(newState);

    if (newState.escaped) {
      await refreshStats();
      setTimeout(() => setShowStats(true), 800);
    }

    setInputWord("");
  }, [game, inputWord, refreshStats, triggerError]);

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
  }, [game, inputWord, submitMove]);

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

  if (!game) return <h2>{message || "Loading..."}</h2>;

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
                .map((letter, letterIndex) => {
                  const tileType = rowIndex === 0
                    ? "start-tile"
                    : word[letterIndex] === game.start_word[letterIndex]
                    ? "retained-tile"
                    : "escaped-tile";
                  const shouldFlip = rowIndex === revealedMove?.rowIndex
                    && letterIndex === revealedMove?.letterIndex;

                  return (
                    <div
                      key={letterIndex}
                      className={`tile ${tileType}${shouldFlip ? " flip-reveal" : ""}`}
                    >
                      {letter}
                    </div>
                  );
                })}
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
          <button className="footer-button" onClick={() => { setAccountMessage(""); setShowAccount(true); }}>
            {account ? "Account" : "Sign in"}
          </button>
          <button className="footer-button" onClick={() => setShowSettings(true)}>
            Settings
          </button>
          <a className="footer-button footer-link" href="/privacy.html">
            Privacy
          </a>
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
      {showAccount && (
        <div className="modal-overlay">
          <div className="modal modal-account">
            <button className="close-button" onClick={() => setShowAccount(false)}>✕</button>
            <h2 className="help-title">YOUR ACCOUNT</h2>
            {account ? (
              <>
                <p className="account-copy">Signed in as <strong>{account.email}</strong>. Your completed puzzles are saved to this account.</p>
                <button className="account-action" onClick={signOut}>Sign out</button>
                <button className="account-action account-delete" onClick={deleteAccount}>Delete account and saved progress</button>
              </>
            ) : (
              <>
                <p className="account-copy">Sign in with Google to keep your stats and completed puzzles across devices. You can play without signing in.</p>
                {GOOGLE_CLIENT_ID ? (
                  <div id="google-sign-in-button" className="google-sign-in-button" />
                ) : (
                  <p className="account-copy">Google sign-in is not configured yet.</p>
                )}
              </>
            )}
            <p className="account-message" role="status">{accountMessage}</p>
          </div>
        </div>
      )}

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
