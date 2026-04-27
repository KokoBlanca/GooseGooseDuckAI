from __future__ import annotations

from pathlib import Path
import argparse
import statistics
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from ggd_coach.capture import ScreenCapture  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark screenshot capture speed.")
    parser.add_argument("--frames", type=int, default=120)
    parser.add_argument("--window-title", default=None)
    args = parser.parse_args()

    capture = ScreenCapture(ROOT / "captures", window_title=args.window_title)

    first_frame = capture.grab()
    timings: list[float] = []
    started = time.perf_counter()
    for _ in range(args.frames):
        frame_started = time.perf_counter()
        capture.grab()
        timings.append(time.perf_counter() - frame_started)
    elapsed = time.perf_counter() - started

    fps = args.frames / elapsed
    avg_ms = statistics.mean(timings) * 1000
    p95_ms = statistics.quantiles(timings, n=20)[18] * 1000
    print(f"frame size: {first_frame.width}x{first_frame.height}")
    print(f"source: {first_frame.source}")
    print(f"frames: {args.frames}")
    print(f"elapsed: {elapsed:.3f}s")
    print(f"fps: {fps:.1f}")
    print(f"avg frame: {avg_ms:.2f}ms")
    print(f"p95 frame: {p95_ms:.2f}ms")


if __name__ == "__main__":
    main()
