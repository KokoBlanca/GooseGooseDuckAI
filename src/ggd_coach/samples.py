from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .capture import ScreenCapture
from .models import CaptureResult, Frame, GameState


class SampleStore:
    def __init__(self, root: Path, capture: ScreenCapture) -> None:
        self.root = root
        self.capture = capture
        self.index_path = self.root / "samples.jsonl"

    def save(self, frame: Frame, state: GameState) -> CaptureResult:
        timestamp = frame.created_at.strftime("%Y%m%d_%H%M%S_%f")
        path = self.root / state.value / f"{timestamp}.png"
        result = self.capture.save_frame(frame, path)
        self._write_index(result, state)
        return result

    def _write_index(self, result: CaptureResult, state: GameState) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        record = {
            "created_at": result.created_at.astimezone(timezone.utc).isoformat(),
            "state": state.value,
            "path": str(result.path),
            "width": result.width,
            "height": result.height,
            "source": result.source,
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.index_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
