"""
utils/fps_counter.py
────────────────────
Lightweight FPS counter that computes a rolling average over the last
N frames so the displayed value doesn't jitter wildly every tick.
"""

import time
from collections import deque


class FPSCounter:
    """
    Usage
    -----
        fps = FPSCounter(window=30)
        while capturing:
            fps.update()
            draw_text(f"{fps.get():.0f} FPS")
    """

    def __init__(self, window: int = 30):
        """
        Parameters
        ----------
        window : int
            Number of recent frame-times to average over.
            Larger = smoother readout; smaller = more responsive.
        """
        self._times: deque = deque(maxlen=window)
        self._last: float = time.perf_counter()
        self.frame_count: int = 0          # total frames since construction

    def update(self) -> None:
        """Call exactly once per rendered frame."""
        now = time.perf_counter()
        self._times.append(now - self._last)
        self._last = now
        self.frame_count += 1

    def get(self) -> float:
        """Return the smoothed FPS estimate (0 before the first update)."""
        if not self._times:
            return 0.0
        avg_dt = sum(self._times) / len(self._times)
        return 1.0 / avg_dt if avg_dt > 0 else 0.0
