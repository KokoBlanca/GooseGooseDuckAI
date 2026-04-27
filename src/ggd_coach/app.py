from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path
import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

from .capture import ScreenCapture
from .logger import JsonlLogger
from .models import Frame, GameState, Observation
from .samples import SampleStore
from .state_detector import StateDetector
from .suggestions import SuggestionEngine


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class PreviewUpdate:
    frame: Frame
    fps: float
    detection_state: GameState | None = None
    detection_confidence: float | None = None
    detection_notes: str | None = None


class CoachApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("GGD AI Coach")
        self.geometry("1180x760")
        self.minsize(980, 640)

        window_title = os.environ.get("GGD_WINDOW_TITLE", "Goose Goose Duck")
        self.capture = ScreenCapture(ROOT / "captures", window_title=window_title)
        self.detector = StateDetector()
        self.suggestions = SuggestionEngine()
        self.logger = JsonlLogger(ROOT / "logs" / "coach_observations.jsonl")
        self.samples = SampleStore(ROOT / "captures" / "samples", self.capture)
        self.preview_queue: queue.Queue[PreviewUpdate | Exception] = queue.Queue()
        self.preview_stop = threading.Event()
        self.preview_thread: threading.Thread | None = None
        self.preview_target_fps = float(os.environ.get("GGD_PREVIEW_FPS", "12"))
        self.preview_detect_interval = float(os.environ.get("GGD_DETECT_INTERVAL", "1.0"))
        self.autostart_preview = os.environ.get("GGD_AUTOSTART", "1") != "0"
        self.latest_frame: Frame | None = None
        self.preview_photo = None

        self.state_var = tk.StringVar(value="unknown")
        self.confidence_var = tk.StringVar(value="0.00")
        self.preview_var = tk.StringVar(value="Stopped")
        self.source_var = tk.StringVar(value="No source yet")
        self.screenshot_var = tk.StringVar(value="No capture yet")
        self.sample_state_var = tk.StringVar(value=GameState.UNKNOWN.value)
        self.notes_var = tk.StringVar(value="Click Capture Screen to create the first observation.")
        self.suggestion_var = tk.StringVar(value="Waiting for observation.")
        self.reason_var = tk.StringVar(value="")

        self._build_ui()
        if self.autostart_preview:
            self.after(300, self.start_preview)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(root, text="GGD AI Coach", font=("Segoe UI", 18, "bold"))
        title.pack(anchor=tk.W)

        subtitle = ttk.Label(
            root,
            text="Read-only private-room prototype. No keyboard or mouse control.",
            foreground="#555555",
        )
        subtitle.pack(anchor=tk.W, pady=(2, 16))

        main = ttk.Frame(root)
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=1)

        preview_panel = ttk.LabelFrame(main, text="Live Preview", padding=10)
        preview_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        preview_panel.columnconfigure(0, weight=1)
        preview_panel.rowconfigure(0, weight=1)

        self.preview_image = ttk.Label(
            preview_panel,
            text="Starting preview...",
            anchor=tk.CENTER,
            background="#111111",
            foreground="#dddddd",
        )
        self.preview_image.grid(row=0, column=0, sticky="nsew")

        side = ttk.Frame(main)
        side.grid(row=0, column=1, sticky="nsew")
        side.columnconfigure(0, weight=1)

        status = ttk.LabelFrame(side, text="Current Observation", padding=12)
        status.grid(row=0, column=0, sticky="ew")

        self._add_row(status, "State", self.state_var)
        self._add_row(status, "Confidence", self.confidence_var)
        self._add_row(status, "Preview", self.preview_var)
        self._add_row(status, "Source", self.source_var)
        self._add_row(status, "Screenshot", self.screenshot_var)
        self._add_row(status, "Notes", self.notes_var)

        suggestion = ttk.LabelFrame(side, text="Suggestion", padding=12)
        suggestion.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        side.rowconfigure(1, weight=1)

        suggestion_text = ttk.Label(
            suggestion,
            textvariable=self.suggestion_var,
            wraplength=390,
            font=("Segoe UI", 11),
        )
        suggestion_text.pack(anchor=tk.W, fill=tk.X)

        reason_text = ttk.Label(
            suggestion,
            textvariable=self.reason_var,
            wraplength=390,
            foreground="#555555",
        )
        reason_text.pack(anchor=tk.W, fill=tk.X, pady=(8, 0))

        controls = ttk.Frame(root)
        controls.pack(fill=tk.X, pady=(14, 0))

        capture_button = ttk.Button(controls, text="Capture Screen", command=self.capture_once)
        capture_button.pack(side=tk.LEFT)

        self.start_button = ttk.Button(controls, text="Start Preview", command=self.start_preview)
        self.start_button.pack(side=tk.LEFT, padx=(8, 0))

        self.stop_button = ttk.Button(controls, text="Stop Preview", command=self.stop_preview, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(8, 0))

        state_values = [state.value for state in GameState]
        sample_state = ttk.Combobox(
            controls,
            textvariable=self.sample_state_var,
            values=state_values,
            width=18,
            state="readonly",
        )
        sample_state.pack(side=tk.LEFT, padx=(16, 0))

        sample_button = ttk.Button(controls, text="Save Sample", command=self.save_sample)
        sample_button.pack(side=tk.LEFT, padx=(8, 0))

        quit_button = ttk.Button(controls, text="Quit", command=self.destroy)
        quit_button.pack(side=tk.RIGHT)

    def _add_row(self, parent: ttk.Frame, label: str, value: tk.StringVar) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=3)
        ttk.Label(row, text=f"{label}:", width=12).pack(side=tk.LEFT)
        ttk.Label(row, textvariable=value, wraplength=590).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def capture_once(self) -> None:
        try:
            frame = self.capture.grab()
            self.latest_frame = frame
            filename = frame.created_at.strftime("capture_%Y%m%d_%H%M%S.png")
            capture = self.capture.save_frame(frame, ROOT / "captures" / filename)
        except RuntimeError as exc:
            messagebox.showerror("Capture failed", str(exc))
            return

        detection = self.detector.detect(capture)
        observation = Observation(
            observed_at=datetime.now().astimezone(),
            state=detection.state,
            confidence=detection.confidence,
            screenshot_path=str(capture.path),
            notes=detection.notes,
        )
        suggestion = self.suggestions.suggest(observation)
        self.logger.write_observation(observation, suggestion)

        self.state_var.set(observation.state.value)
        self.confidence_var.set(f"{observation.confidence:.2f}")
        self.source_var.set(capture.source)
        self.screenshot_var.set(str(capture.path))
        self.notes_var.set(observation.notes)
        self.suggestion_var.set(suggestion.message)
        self.reason_var.set(f"Reason: {suggestion.reason}")

    def save_sample(self) -> None:
        if self.latest_frame is None:
            try:
                self.latest_frame = self.capture.grab()
            except RuntimeError as exc:
                messagebox.showerror("Sample failed", str(exc))
                return

        try:
            state = GameState(self.sample_state_var.get())
        except ValueError:
            messagebox.showerror("Sample failed", "Choose a valid state label.")
            return

        try:
            result = self.samples.save(self.latest_frame, state)
        except RuntimeError as exc:
            messagebox.showerror("Sample failed", str(exc))
            return

        self.screenshot_var.set(str(result.path))
        self.notes_var.set(f"Saved labeled sample as {state.value}.")

    def start_preview(self) -> None:
        if self.preview_thread and self.preview_thread.is_alive():
            return

        self._clear_preview_queue()
        self.preview_stop.clear()
        self.preview_thread = threading.Thread(target=self._preview_loop, daemon=True)
        self.preview_thread.start()
        self.preview_var.set("Starting...")
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.after(50, self._poll_preview_queue)

    def stop_preview(self) -> None:
        self.preview_stop.set()
        self.preview_var.set("Stopping...")
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.DISABLED)

    def _preview_loop(self) -> None:
        min_interval = 1.0 / max(self.preview_target_fps, 1.0)
        last_frame_at: float | None = None
        last_detection_at = 0.0
        while not self.preview_stop.is_set():
            frame_started = time.perf_counter()
            try:
                frame = self.capture.grab()
                now = time.perf_counter()
                fps = 0.0 if last_frame_at is None else 1.0 / max(now - last_frame_at, 0.0001)
                last_frame_at = now
                detection = None
                if now - last_detection_at >= self.preview_detect_interval:
                    detection = self.detector.detect_frame(frame)
                    last_detection_at = now

                self._replace_preview_update(
                    PreviewUpdate(
                        frame=frame,
                        fps=fps,
                        detection_state=detection.state if detection else None,
                        detection_confidence=detection.confidence if detection else None,
                        detection_notes=detection.notes if detection else None,
                    )
                )
            except Exception as exc:  # pragma: no cover - defensive UI boundary
                self._replace_preview_update(exc)
                self.preview_stop.set()
                break

            elapsed = time.perf_counter() - frame_started
            remaining = min_interval - elapsed
            if remaining > 0:
                time.sleep(remaining)

    def _replace_preview_update(self, update: PreviewUpdate | Exception) -> None:
        self._clear_preview_queue()
        self.preview_queue.put(update)

    def _clear_preview_queue(self) -> None:
        while True:
            try:
                self.preview_queue.get_nowait()
            except queue.Empty:
                break

    def _poll_preview_queue(self) -> None:
        try:
            update = self.preview_queue.get_nowait()
        except queue.Empty:
            update = None

        if isinstance(update, Exception):
            self.preview_var.set("Stopped after error")
            self.preview_thread = None
            self.start_button.configure(state=tk.NORMAL)
            self.stop_button.configure(state=tk.DISABLED)
            messagebox.showerror("Preview failed", str(update))
            return

        if isinstance(update, PreviewUpdate):
            frame = update.frame
            self.latest_frame = frame
            self.preview_var.set(f"{update.fps:.1f} FPS | {frame.width}x{frame.height}")
            self.source_var.set(frame.source)
            self.screenshot_var.set("Preview uses memory frames only")
            self._render_preview_frame(frame)
            if update.detection_state is not None:
                self.state_var.set(update.detection_state.value)
                self.confidence_var.set(f"{update.detection_confidence:.2f}")
                self.notes_var.set(update.detection_notes or "")
                observation = Observation(
                    observed_at=datetime.now().astimezone(),
                    state=update.detection_state,
                    confidence=update.detection_confidence or 0.0,
                    screenshot_path=None,
                    notes=update.detection_notes or "",
                )
                suggestion = self.suggestions.suggest(observation)
                self.suggestion_var.set(suggestion.message)
                self.reason_var.set(f"Reason: {suggestion.reason}")

        if self.preview_stop.is_set():
            if self.preview_thread and self.preview_thread.is_alive():
                self.preview_var.set("Stopping...")
                self.after(50, self._poll_preview_queue)
                return

            self.preview_thread = None
            self.preview_var.set("Stopped")
            self.start_button.configure(state=tk.NORMAL)
            self.stop_button.configure(state=tk.DISABLED)
            return

        self.after(50, self._poll_preview_queue)

    def destroy(self) -> None:
        self.preview_stop.set()
        super().destroy()

    def _render_preview_frame(self, frame: Frame) -> None:
        try:
            from PIL import Image, ImageTk
        except ImportError:
            self.preview_image.configure(text="Pillow is required for live preview image.")
            return

        width = max(self.preview_image.winfo_width(), 320)
        height = max(self.preview_image.winfo_height(), 240)
        image = Image.frombytes("RGBA", (frame.width, frame.height), frame.data, "raw", "BGRA")
        image.thumbnail((width, height), Image.Resampling.BILINEAR)
        self.preview_photo = ImageTk.PhotoImage(image)
        self.preview_image.configure(image=self.preview_photo, text="")


def main() -> None:
    app = CoachApp()
    app.mainloop()
