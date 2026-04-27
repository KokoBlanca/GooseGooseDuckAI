from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from ggd_coach.logger import JsonlLogger  # noqa: E402
from ggd_coach.models import CaptureResult, GameState, Observation  # noqa: E402
from ggd_coach.state_detector import StateDetector  # noqa: E402
from ggd_coach.suggestions import SuggestionEngine  # noqa: E402


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
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

        observation = Observation(
            observed_at=datetime.now().astimezone(),
            state=detection.state,
            confidence=detection.confidence,
            screenshot_path=str(capture.path),
            notes=detection.notes,
        )
        suggestion = SuggestionEngine().suggest(observation)
        assert suggestion.action == "pause"

        log_path = tmp_path / "coach.jsonl"
        JsonlLogger(log_path).write_observation(observation, suggestion)
        record = json.loads(log_path.read_text(encoding="utf-8"))
        assert record["observation"]["state"] == "unknown"
        assert record["suggestion"]["action"] == "pause"

    print("smoke test ok")


if __name__ == "__main__":
    main()
