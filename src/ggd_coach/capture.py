from __future__ import annotations

from datetime import datetime
from pathlib import Path
import threading

from .models import CaptureResult, Frame
from .window_finder import WindowRect, find_window_by_title


class ScreenCapture:
    """Fast screenshot capture.

    The realtime path is grab(), which returns an in-memory BGRA frame and does
    not write to disk. capture() is only for manual debugging snapshots.
    """

    def __init__(self, output_dir: Path, window_title: str | None = None) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.window_title = window_title
        self._local = threading.local()

    def _ensure_mss(self):
        try:
            import mss
        except ImportError as exc:
            raise RuntimeError(
                "Fast capture needs mss. Install it with: python -m pip install mss"
            ) from exc

        if not hasattr(self._local, "sct"):
            self._local.sct = mss.mss()
        sct = self._local.sct
        return sct, sct.monitors[1]

    def _current_monitor(self) -> tuple[dict[str, int], str]:
        _sct, monitor = self._ensure_mss()
        if self.window_title:
            window = find_window_by_title(self.window_title)
            if window is not None:
                return window.to_mss_monitor(), self._format_window_source(window)
        return monitor, "primary_monitor"

    def _format_window_source(self, window: WindowRect) -> str:
        return (
            f'window "{window.title}" '
            f"({window.left},{window.top} {window.width}x{window.height})"
        )

    def grab(self) -> Frame:
        sct, _monitor = self._ensure_mss()
        monitor, source = self._current_monitor()
        created_at = datetime.now().astimezone()
        screenshot = sct.grab(monitor)
        return Frame(
            width=screenshot.width,
            height=screenshot.height,
            created_at=created_at,
            data=screenshot.bgra,
            source=source,
        )

    def capture(self) -> CaptureResult:
        frame = self.grab()
        try:
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError(
                "Saving debug captures needs Pillow. Install it with: python -m pip install pillow"
            ) from exc

        created_at = datetime.now().astimezone()
        filename = created_at.strftime("capture_%Y%m%d_%H%M%S.png")
        path = self.output_dir / filename
        image = Image.frombytes("RGBA", (frame.width, frame.height), frame.data, "raw", "BGRA")
        image.save(path)
        return CaptureResult(
            path=path,
            width=frame.width,
            height=frame.height,
            created_at=created_at,
            source=frame.source,
        )
