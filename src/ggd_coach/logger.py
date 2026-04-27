from __future__ import annotations

import json
from pathlib import Path

from .models import Observation, Suggestion


class JsonlLogger:
    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def write_observation(self, observation: Observation, suggestion: Suggestion) -> None:
        record = {
            "type": "coach_observation",
            "observation": observation.to_json(),
            "suggestion": suggestion.to_json(),
        }
        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
