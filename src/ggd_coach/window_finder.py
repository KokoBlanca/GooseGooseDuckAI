from __future__ import annotations

from dataclasses import dataclass
import ctypes
from ctypes import wintypes
import os


@dataclass(frozen=True)
class WindowRect:
    left: int
    top: int
    width: int
    height: int
    title: str
    process_id: int

    def to_mss_monitor(self) -> dict[str, int]:
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }


def list_visible_windows() -> list[WindowRect]:
    user32 = ctypes.windll.user32
    windows: list[WindowRect] = []

    enum_windows_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True

        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True

        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value

        rect = wintypes.RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return True

        width = rect.right - rect.left
        height = rect.bottom - rect.top
        if width <= 0 or height <= 0:
            return True

        process_id = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))

        windows.append(
            WindowRect(
                left=rect.left,
                top=rect.top,
                width=width,
                height=height,
                title=title,
                process_id=process_id.value,
            )
        )
        return True

    user32.EnumWindows(enum_windows_proc(callback), 0)
    return windows


def find_window_by_title(
    title_part: str,
    exclude_current_process: bool = True,
    exclude_title_parts: tuple[str, ...] = ("AI Coach",),
) -> WindowRect | None:
    if not title_part:
        return None

    title_part_lower = title_part.lower()
    current_pid = os.getpid()
    windows = list_visible_windows()
    if exclude_current_process:
        windows = [window for window in windows if window.process_id != current_pid]
    if exclude_title_parts:
        lowered_excludes = tuple(part.lower() for part in exclude_title_parts)
        windows = [
            window
            for window in windows
            if not any(part in window.title.lower() for part in lowered_excludes)
        ]

    exact_matches = [window for window in windows if window.title.lower() == title_part_lower]
    if exact_matches:
        return exact_matches[0]

    contains_matches = [window for window in windows if title_part_lower in window.title.lower()]
    return contains_matches[0] if contains_matches else None
