from __future__ import annotations

from .models import CaptureResult, GameState


class StateDetector:
    """Placeholder high-level game state detector.

    The first version is deliberately conservative. It produces UNKNOWN until
    we add image features or OCR for specific Goose Goose Duck screens.
    """

    def detect(self, capture: CaptureResult | None) -> tuple[GameState, float, str]:
        if capture is None:
            return GameState.UNKNOWN, 0.0, "No screenshot captured yet."

        if capture.width <= 0 or capture.height <= 0:
            return GameState.UNKNOWN, 0.0, "Screenshot dimensions are invalid."

        return (
            GameState.UNKNOWN,
            0.2,
            f"Screenshot captured from {capture.source}, but visual state detection is not implemented yet.",
        )
