from __future__ import annotations

from pathlib import Path
import argparse
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from ggd_coach.window_finder import list_visible_windows  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="List visible Windows desktop windows.")
    parser.add_argument("--filter", default="", help="Optional case-insensitive title filter.")
    args = parser.parse_args()

    title_filter = args.filter.lower()
    windows = list_visible_windows()
    if title_filter:
        windows = [window for window in windows if title_filter in window.title.lower()]

    for index, window in enumerate(windows, start=1):
        print(
            f"{index:02d}. {window.width}x{window.height} "
            f"at ({window.left},{window.top}) | pid={window.process_id} | {window.title}"
        )

    if not windows:
        print("No matching visible windows found.")


if __name__ == "__main__":
    main()
