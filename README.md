# Goose Goose Duck AI Coach

Private-room AI filler project for Goose Goose Duck.

The first milestone is a read-only Coach prototype:

- Capture the screen with a fast in-memory path.
- Run a continuous preview loop without saving every frame.
- Detect a rough game state.
- Save timestamped observations.
- Show a conservative suggestion.

This project is intended only for friend rooms where everyone knows an AI is filling a seat. It does not read game memory, inspect packets, inject into the game, or bypass anti-cheat.

## Run

```powershell
python run_coach.py
```

By default the app tries to capture a window whose title contains `Goose Goose Duck`. You can override that title:

```powershell
$env:GGD_WINDOW_TITLE = "Goose Goose Duck"
$env:GGD_PREVIEW_FPS = "15"
python run_coach.py
```

Or run the package directly:

```powershell
$env:PYTHONPATH = "src"
python -m ggd_coach
```

## Verify

```powershell
python scripts/smoke_test.py
python -m pytest -q
python scripts/list_windows.py --filter "Goose"
python scripts/benchmark_capture.py
python scripts/benchmark_capture.py --window-title "Goose Goose Duck"
```

## Current Status

Phase 1 is just beginning. The app can start, capture the desktop with a manual button, log observations, and return a placeholder state/suggestion. Realtime capture now uses `mss` in memory; the debug button saves a PNG only when clicked. The app also has a continuous preview loop for testing capture speed without writing frames to disk. The next step is to add real UI state detection.
