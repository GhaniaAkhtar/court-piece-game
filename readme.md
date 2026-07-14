# Court Piece 🃏

A full-stack implementation of **Court Piece** (a South Asian trick-taking card game), built from scratch as a learning project — starting from a plain console game and evolving into a fully playable browser-based game with a Python backend.

## What's included

- **Game engine** (`game.py`) — deck creation, dealer selection, trump selection, turn rotation, follow-suit enforcement, trick-winner logic, and scoring, all built and tested first as a console game.
- **Backend API** (`api.py`) — a FastAPI server that exposes the game engine as REST endpoints, tracking game state (whose turn it is, hands, scores, trick history) between requests.
- **Frontend** (`index.html`) — a single-page browser interface with a live 4-player table layout, real playing card images, sound effects, confetti/applause on a round win, and turn-by-turn enforcement of legal moves.

## Current status

✅ **Level 1 — 4 human players** (pass-and-play on one screen) is fully working, end to end: dealer selection → trump selection → dealing → trick-by-trick play → round winner.

⬜ **Level 2 — AI opponents** is planned but not yet built.

## How to run it locally

**1. Install dependencies**
```bash
pip install fastapi uvicorn
```

**2. Start the backend server**

In the project folder, run:
```bash
uvicorn api:app --reload
```
Leave this running — it starts a local server at `http://127.0.0.1:8000`.

**3. Open the game**

Open `index.html` directly in your browser (just double-click it, or right-click → Open with → your browser).

**4. Play**

Click **Start Game** and follow the on-screen prompts — dealer gets picked automatically, then the trump selector chooses a suit, then the game deals and play begins. Since this is a pass-and-play game, all 4 players take turns on the same screen.

## Tech stack

- **Backend:** Python, FastAPI, Uvicorn
- **Frontend:** Plain HTML, CSS, and JavaScript (no frameworks)
- **Card images:** [deckofcardsapi.com](https://deckofcardsapi.com)

## Notes

- The server needs to stay running in a terminal while you play — closing it or restarting it (e.g. by editing `api.py`) resets the current game.
- This is a local, single-machine game for now (all 4 players share one screen/browser tab) — it isn't deployed online yet.

---

Built as a self-directed learning project to practice game logic, API design, and frontend integration.