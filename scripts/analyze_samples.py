from __future__ import annotations

from datetime import datetime
from pathlib import Path
import argparse
import json
import statistics
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from ggd_coach.models import Frame  # noqa: E402
from ggd_coach.state_detector import FrameAnalyzer  # noqa: E402


def frame_from_png(path: Path) -> Frame:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required to analyze samples.") from exc

    image = Image.open(path).convert("RGBA")
    return Frame(
        width=image.width,
        height=image.height,
        created_at=datetime.fromtimestamp(path.stat().st_mtime).astimezone(),
        data=image.tobytes("raw", "BGRA"),
        source=str(path),
    )


def summarize(values: list[float]) -> str:
    if not values:
        return "n/a"
    return f"avg={statistics.mean(values):.3f}, min={min(values):.3f}, max={max(values):.3f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze labeled frame samples.")
    parser.add_argument("--samples-dir", default=str(ROOT / "captures" / "samples"))
    args = parser.parse_args()

    samples_dir = Path(args.samples_dir)
    index_path = samples_dir / "samples.jsonl"
    if not index_path.exists():
        print(f"No sample index found: {index_path}")
        return

    analyzer = FrameAnalyzer()
    by_state: dict[str, list[dict[str, float]]] = {}
    for line in index_path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        path = Path(record["path"])
        if not path.exists():
            continue
        features = analyzer.analyze(frame_from_png(path)).to_json()
        by_state.setdefault(record["state"], []).append(features)

    for state, feature_rows in sorted(by_state.items()):
        print(f"\n{state} ({len(feature_rows)} samples)")
        for key in (
            "mean_brightness",
            "dark_ratio",
            "bright_ratio",
            "red_ratio",
            "green_ratio",
            "blue_ratio",
        ):
            print(f"  {key}: {summarize([row[key] for row in feature_rows])}")


if __name__ == "__main__":
    main()
