# Goose Goose Duck AI Coach

Private-room AI filler project for Goose Goose Duck.

The first milestone is a read-only Coach prototype:

- Capture the screen with a fast in-memory path.
- Run a continuous preview loop without saving every frame.
- Save labeled frame samples for state detection training/rules.
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
$env:GGD_PREVIEW_FPS = "12"
$env:GGD_AUTOSTART = "1"
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
python scripts/analyze_samples.py
```

## Current Status

Phase 1 is just beginning. The app can start, show a live game-window preview, capture debug screenshots with a manual button, log observations, and return a placeholder state/suggestion. Realtime capture now uses `mss` in memory; the debug button saves a PNG only when clicked. The app also has a continuous preview loop for testing capture speed without writing frames to disk. The next step is to add real UI state detection.

For state detection work, run preview during a private test session, choose a label from the dropdown, and click `Save Sample`. Samples are stored under `captures/samples/<state>/` and indexed in `captures/samples/samples.jsonl`. Once samples exist, run `python scripts/analyze_samples.py` to compare basic visual features by state.
