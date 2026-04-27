from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any


class GameState(StrEnum):
    LOBBY = "lobby"
    FREE_MOVEMENT = "free_movement"
    MEETING = "meeting"
    VOTING = "voting"
    DEAD_OR_GHOST = "dead_or_ghost"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CaptureResult:
    path: Path
    width: int
    height: int
    created_at: datetime
    source: str


@dataclass(frozen=True)
class Frame:
    width: int
    height: int
    created_at: datetime
    data: bytes
    pixel_format: str = "BGRA"
    source: str = "primary_monitor"


@dataclass(frozen=True)
class FrameFeatures:
    sampled_pixels: int
    mean_brightness: float
    dark_ratio: float
    bright_ratio: float
    red_ratio: float
    green_ratio: float
    blue_ratio: float

    def to_json(self) -> dict[str, Any]:
        return {
            "sampled_pixels": self.sampled_pixels,
            "mean_brightness": round(self.mean_brightness, 4),
            "dark_ratio": round(self.dark_ratio, 4),
            "bright_ratio": round(self.bright_ratio, 4),
            "red_ratio": round(self.red_ratio, 4),
            "green_ratio": round(self.green_ratio, 4),
            "blue_ratio": round(self.blue_ratio, 4),
        }


@dataclass(frozen=True)
class DetectionResult:
    state: GameState
    confidence: float
    notes: str
    features: FrameFeatures | None = None


@dataclass(frozen=True)
class Observation:
    observed_at: datetime
    state: GameState
    confidence: float
    screenshot_path: str | None
    notes: str

    def to_json(self) -> dict[str, Any]:
        return {
            "observed_at": self.observed_at.astimezone(timezone.utc).isoformat(),
            "state": self.state.value,
            "confidence": self.confidence,
            "screenshot_path": self.screenshot_path,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class Suggestion:
    action: str
    confidence: float
    message: str
    reason: str

    def to_json(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "confidence": self.confidence,
            "message": self.message,
            "reason": self.reason,
        }
