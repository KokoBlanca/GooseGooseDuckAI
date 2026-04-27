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
        state, confidence, notes = StateDetector().detect(capture)
        assert state == GameState.UNKNOWN
        assert confidence == 0.2
        assert "not implemented" in notes

        observation = Observation(
            observed_at=datetime.now().astimezone(),
            state=state,
            confidence=confidence,
            screenshot_path=str(capture.path),
            notes=notes,
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
