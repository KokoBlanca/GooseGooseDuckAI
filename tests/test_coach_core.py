from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ggd_coach.logger import JsonlLogger
from ggd_coach.game_memory import GameMemory
from ggd_coach.models import CaptureResult, Frame, GameState, Observation
from ggd_coach.samples import SampleStore
from ggd_coach.state_detector import FrameAnalyzer, StateDetector
from ggd_coach.suggestions import SuggestionEngine


def test_state_detector_returns_unknown_for_first_placeholder_capture(tmp_path: Path) -> None:
    capture = CaptureResult(
        path=tmp_path / "capture.png",
        width=1920,
        height=1080,
        created_at=datetime.now().astimezone(),
        source="test",
    )

    detection = StateDetector().detect(capture)

    assert detection.state == GameState.UNKNOWN
    assert detection.confidence == 0.2
    assert "frame features" in detection.notes


def test_frame_analyzer_extracts_basic_color_features() -> None:
    frame = Frame(
        width=2,
        height=1,
        created_at=datetime.now().astimezone(),
        data=bytes(
            [
                0,
                0,
                255,
                255,
                0,
                0,
                0,
                255,
            ]
        ),
    )

    features = FrameAnalyzer().analyze(frame)

    assert features.sampled_pixels == 2
    assert features.red_ratio == 0.5
    assert features.dark_ratio == 0.5


def test_state_detector_analyzes_frame_conservatively() -> None:
    frame = Frame(
        width=1,
        height=1,
        created_at=datetime.now().astimezone(),
        data=bytes([255, 255, 255, 255]),
    )

    detection = StateDetector().detect_frame(frame)

    assert detection.state == GameState.UNKNOWN
    assert detection.features is not None
    assert detection.features.bright_ratio == 1.0


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


def test_sample_store_writes_state_index(tmp_path: Path) -> None:
    class FakeCapture:
        def save_frame(self, frame, path):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"fake")
            return CaptureResult(
                path=path,
                width=frame.width,
                height=frame.height,
                created_at=frame.created_at,
                source=frame.source,
            )

    frame = Frame(
        width=2,
        height=2,
        created_at=datetime.now().astimezone(),
        data=b"\x00" * 16,
        source="test",
    )
    store = SampleStore(tmp_path / "samples", FakeCapture())

    result = store.save(frame, GameState.MEETING)

    assert result.path.exists()
    assert result.path.parent.name == "meeting"
    index = (tmp_path / "samples" / "samples.jsonl").read_text(encoding="utf-8")
    assert '"state": "meeting"' in index


def test_game_memory_ranks_suspicious_players_and_suggests_questioning() -> None:
    memory = GameMemory()
    memory.add_event("seen", "Alice", "kitchen")
    memory.add_event("suspicious", "Bob", "near body")
    memory.add_event("suspicious", "Bob", "changed route claim")

    suggestion, reason = memory.suggestion()

    assert "Bob" in suggestion
    assert "Bob" in reason
    assert memory.ranked_players()[0].name == "Bob"
