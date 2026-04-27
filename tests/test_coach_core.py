from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ggd_coach.logger import JsonlLogger
from ggd_coach.models import CaptureResult, GameState, Observation
from ggd_coach.state_detector import StateDetector
from ggd_coach.suggestions import SuggestionEngine


def test_state_detector_returns_unknown_for_first_placeholder_capture(tmp_path: Path) -> None:
    capture = CaptureResult(
        path=tmp_path / "capture.png",
        width=1920,
        height=1080,
        created_at=datetime.now().astimezone(),
        source="test",
    )

    state, confidence, notes = StateDetector().detect(capture)

    assert state == GameState.UNKNOWN
    assert confidence == 0.2
    assert "not implemented" in notes


def test_suggestion_engine_pauses_on_unknown_state() -> None:
    observation = Observation(
        observed_at=datetime.now().astimezone(),
        state=GameState.UNKNOWN,
        confidence=0.2,
        screenshot_path=None,
        notes="Unknown screen",
    )

    suggestion = SuggestionEngine().suggest(observation)

    assert suggestion.action == "pause"
    assert "暂停" in suggestion.message


def test_jsonl_logger_writes_observation_and_suggestion(tmp_path: Path) -> None:
    observation = Observation(
        observed_at=datetime.now().astimezone(),
        state=GameState.UNKNOWN,
        confidence=0.2,
        screenshot_path="captures/example.png",
        notes="Unknown screen",
    )
    suggestion = SuggestionEngine().suggest(observation)
    log_path = tmp_path / "coach.jsonl"

    JsonlLogger(log_path).write_observation(observation, suggestion)

    record = json.loads(log_path.read_text(encoding="utf-8"))
    assert record["type"] == "coach_observation"
    assert record["observation"]["state"] == "unknown"
    assert record["suggestion"]["action"] == "pause"
