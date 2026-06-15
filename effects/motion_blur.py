"""
effects/motion_blur.py
──────────────────────
Applies a directional motion-blur effect to simulate speed during zoom.

How it works
─────────────
We build a 1-D convolution kernel oriented at a given angle.
The kernel is applied with cv2.filter2D, which convolves each pixel with
its neighbours along the blur direction — mimicking the streaks you see
in a fast-moving photograph.

Kernel size scales with zoom velocity so blur is subtle at slow zoom
speeds and dramatic at peak velocity.
"""

import math
import numpy as np
import cv2
from utils.config import Config


class MotionBlur:
    """
    Usage
    -----
        blur = MotionBlur()
        if zooming:
            frame = blur.apply(frame, zoom_velocity)
    """

    def __init__(self):
        cfg = Config()
        self._max_kernel = cfg.BLUR_MAX_KERNEL   # caps at this odd integer
        self._angle_deg  = cfg.BLUR_DIRECTION_ANGLE

    def apply(self, frame: np.ndarray, velocity: float) -> np.ndarray:
        """
        Apply motion blur proportional to `velocity`.

        Parameters
        ----------
        frame    : BGR image array
        velocity : float ≥ 0  — zoom rate of change this frame.
                   Typically 0.00–0.05; values above ~0.03 produce
                   clearly visible streaks.

        Returns
        -------
        Blurred BGR frame.
        """
        # Scale: velocity of 0.05 → full BLUR_MAX_KERNEL size
        scale = min(velocity / 0.05, 1.0)
        kernel_size = int(scale * self._max_kernel)

        # Kernel must be a positive odd integer
        kernel_size = max(1, kernel_size | 1)    # |1 makes it odd

        if kernel_size <= 1:
            return frame    # nothing to do

        kernel = self._make_kernel(kernel_size, self._angle_deg)
        return cv2.filter2D(frame, -1, kernel)

    # ── Private ───────────────────────────────────────────────────────────────

    @staticmethod
    def _make_kernel(size: int, angle_deg: float) -> np.ndarray:
        """
        Build a normalised linear-motion blur kernel.

        A 1-D line is drawn through a square zero matrix at `angle_deg`
        degrees (0 = horizontal, 90 = vertical).  The non-zero cells
        are normalised so the filter preserves overall brightness.

        Parameters
        ----------
        size      : odd int — kernel side length
        angle_deg : float   — streak direction in degrees
        """
        kernel = np.zeros((size, size), dtype=np.float32)
        centre = size // 2

        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        for t in range(-centre, centre + 1):
            x = int(round(centre + t * cos_a))
            y = int(round(centre + t * sin_a))
            if 0 <= x < size and 0 <= y < size:
                kernel[y, x] = 1.0

        total = kernel.sum()
        if total > 0:
            kernel /= total

        return kernel
