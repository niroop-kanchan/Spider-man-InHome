"""
core/zoom_controller.py

Handles the gesture-lock pull zoom:
1. The web gesture appears.
2. The current hand size is locked as the reference.
3. If the gesture stays visible and the hand is pulled backward, the hand
   appears smaller and the camera zooms.
4. Once the pull reaches the high range, zoom locks near 145-150% until
   the gesture is released.
"""

import math
import random
import numpy as np
import cv2
from utils.config import Config


class ZoomController:
    """Stateful pull-to-zoom controller."""

    def __init__(self, cfg: Config):
        self._cfg = cfg

        self._current_zoom: float = 1.0
        self._target_zoom: float = 1.0
        self._prev_zoom: float = 1.0

        self._ref_y: float = -1.0
        self._ref_scale: float = -1.0
        self._was_active: bool = False
        self._zoom_locked: bool = False

        self._shake_x: float = 0.0
        self._shake_y: float = 0.0
        self._shake_mag: float = 0.0

    def update(self, web_active: bool, wrist_pos: tuple,
               frame_h: int, hand_scale: float = 0.0) -> None:
        """Update target zoom from the active gesture hand."""
        _, wy = wrist_pos

        if web_active:
            if not self._was_active:
                self._ref_y = wy
                self._ref_scale = max(1.0, hand_scale)
                self._zoom_locked = False
                if self._cfg.SHAKE_ENABLED:
                    self._shake_mag = float(self._cfg.SHAKE_MAGNITUDE)

            pull_norm = 0.0
            if hand_scale > 0 and self._ref_scale > 0:
                pull_norm = (1.0 - (hand_scale / self._ref_scale)) / 0.30
                pull_norm = max(0.0, min(pull_norm, 1.0))

            if pull_norm >= 0.85:
                self._zoom_locked = True

            if self._zoom_locked:
                self._target_zoom = self._cfg.MAX_ZOOM
            else:
                self._target_zoom = 1.0 + pull_norm * (self._cfg.MAX_ZOOM - 1.0)

            self._was_active = True
        else:
            self._target_zoom = 1.0
            self._ref_y = -1.0
            self._ref_scale = -1.0
            self._was_active = False
            self._zoom_locked = False

        speed = self._cfg.ZOOM_SPEED if web_active else self._cfg.ZOOM_RELEASE_SPEED
        self._prev_zoom = self._current_zoom
        self._current_zoom = _lerp(self._current_zoom, self._target_zoom, speed)

        if self._shake_mag > 0.5:
            angle = random.uniform(0, 2 * math.pi)
            self._shake_x = math.cos(angle) * self._shake_mag
            self._shake_y = math.sin(angle) * self._shake_mag
            self._shake_mag *= self._cfg.SHAKE_DECAY
        else:
            self._shake_mag = 0.0
            self._shake_x = 0.0
            self._shake_y = 0.0

    def apply(self, frame: np.ndarray) -> np.ndarray:
        """Apply the current zoom and optional shake to a BGR frame."""
        h, w = frame.shape[:2]
        z = self._current_zoom

        if abs(z - 1.0) < 0.001 and abs(self._shake_x) < 0.5:
            return frame

        cx = w / 2 + self._shake_x
        cy = h / 2 + self._shake_y
        cw = w / z
        ch = h / z

        x1 = int(cx - cw / 2)
        y1 = int(cy - ch / 2)
        x2 = int(cx + cw / 2)
        y2 = int(cy + ch / 2)

        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)

        cropped = frame[y1:y2, x1:x2]
        if cropped.size == 0:
            return frame

        return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

    def get_zoom_level(self) -> float:
        return self._current_zoom

    def is_zooming(self) -> bool:
        return self._current_zoom > 1.05

    def zoom_velocity(self) -> float:
        return abs(self._current_zoom - self._prev_zoom)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t
