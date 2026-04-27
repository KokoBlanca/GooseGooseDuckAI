from __future__ import annotations

from .models import CaptureResult, DetectionResult, Frame, FrameFeatures, GameState


class FrameAnalyzer:
    """Extract cheap visual features from BGRA frames.

    This is intentionally lightweight so the preview loop can run it regularly
    without turning capture into a CPU tax. The first detector remains
    conservative until we have labeled samples from the actual game.
    """

    def analyze(self, frame: Frame, max_samples: int = 12000) -> FrameFeatures:
        if frame.pixel_format != "BGRA":
            raise ValueError(f"Unsupported pixel format: {frame.pixel_format}")
        if frame.width <= 0 or frame.height <= 0:
            raise ValueError("Frame dimensions are invalid.")

        total_pixels = frame.width * frame.height
        stride = max(1, total_pixels // max_samples)

        sampled = 0
        brightness_sum = 0.0
        dark = 0
        bright = 0
        red = 0
        green = 0
        blue = 0

        for pixel_index in range(0, total_pixels, stride):
            offset = pixel_index * 4
            b = frame.data[offset]
            g = frame.data[offset + 1]
            r = frame.data[offset + 2]
            brightness = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
            brightness_sum += brightness
            sampled += 1

            if brightness < 0.18:
                dark += 1
            if brightness > 0.78:
                bright += 1
            if r > 150 and r > g * 1.25 and r > b * 1.25:
                red += 1
            if g > 150 and g > r * 1.2 and g > b * 1.2:
                green += 1
            if b > 150 and b > r * 1.2 and b > g * 1.2:
                blue += 1

        return FrameFeatures(
            sampled_pixels=sampled,
            mean_brightness=brightness_sum / max(sampled, 1),
            dark_ratio=dark / max(sampled, 1),
            bright_ratio=bright / max(sampled, 1),
            red_ratio=red / max(sampled, 1),
            green_ratio=green / max(sampled, 1),
            blue_ratio=blue / max(sampled, 1),
        )


class StateDetector:
    """Placeholder high-level game state detector.

    The first version is deliberately conservative. It produces UNKNOWN until
    we add image features or OCR for specific Goose Goose Duck screens.
    """

    def __init__(self, analyzer: FrameAnalyzer | None = None) -> None:
        self.analyzer = analyzer or FrameAnalyzer()

    def detect(self, capture: CaptureResult | None) -> DetectionResult:
        if capture is None:
            return DetectionResult(GameState.UNKNOWN, 0.0, "No screenshot captured yet.")

        if capture.width <= 0 or capture.height <= 0:
            return DetectionResult(GameState.UNKNOWN, 0.0, "Screenshot dimensions are invalid.")

        return DetectionResult(
            state=GameState.UNKNOWN,
            confidence=0.2,
            notes=f"Screenshot captured from {capture.source}, but visual state detection needs frame features.",
        )

    def detect_frame(self, frame: Frame) -> DetectionResult:
        features = self.analyzer.analyze(frame)
        notes = (
            "Frame analyzed; waiting for labeled samples before assigning a specific state. "
            f"brightness={features.mean_brightness:.2f}, "
            f"dark={features.dark_ratio:.2f}, bright={features.bright_ratio:.2f}, "
            f"red={features.red_ratio:.2f}"
        )
        return DetectionResult(
            state=GameState.UNKNOWN,
            confidence=0.25,
            notes=notes,
            features=features,
        )
