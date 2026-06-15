"""
effects/web_renderer.py

Draws a slim white Spider-Man style web from the wrist, aimed in the
direction the web gesture hand is pointing.
"""

import math
import numpy as np
import cv2
from utils.config import Config


class WebRenderer:
    """Draws a thin web cone from one or both gesture hands."""

    WRIST = 0
    INDEX_TIP = 8
    PINKY_TIP = 20

    def __init__(self, cfg: Config):
        self._cfg = cfg
        self._progress: float = 0.0
        self._was_active: bool = False

    def draw_many(self, frame: np.ndarray,
                  hands_landmarks: list,
                  frame_w: int, frame_h: int) -> np.ndarray:
        """
        Draw a slim web for every active gesture hand.
        The web starts at the wrist and follows the hand's aim direction.
        """
        if not hands_landmarks:
            self.reset()
            return frame

        if not self._was_active:
            self._progress = 0.0
        self._progress = min(1.0, self._progress + self._cfg.WEB_GROW_SPEED)
        self._was_active = True

        overlay = frame.copy()
        for landmarks in hands_landmarks:
            self._draw_one(overlay, landmarks, frame_w, frame_h)

        alpha = 0.78 + 0.18 * self._progress
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        return frame

    def draw(self, frame: np.ndarray,
             wrist_pos: tuple,
             frame_w: int, frame_h: int) -> np.ndarray:
        """Backward-compatible fallback for old single-wrist calls."""
        wx, wy = wrist_pos
        fake_hand = [(wx, wy)] * 21
        fake_hand[self.INDEX_TIP] = (wx, max(0, wy - 1))
        fake_hand[self.PINKY_TIP] = (wx, max(0, wy - 1))
        return self.draw_many(frame, [fake_hand], frame_w, frame_h)

    def _draw_one(self, overlay: np.ndarray,
                  landmarks: list,
                  frame_w: int, frame_h: int) -> None:
        wrist = landmarks[self.WRIST]
        index_tip = landmarks[self.INDEX_TIP]
        pinky_tip = landmarks[self.PINKY_TIP]

        aim_x = (index_tip[0] + pinky_tip[0]) / 2.0
        aim_y = (index_tip[1] + pinky_tip[1]) / 2.0

        dx = aim_x - wrist[0]
        dy = aim_y - wrist[1]
        length = math.hypot(dx, dy)

        if length < 1.0:
            dx, dy = 0.0, -1.0
            length = 1.0

        dx /= length
        dy /= length
        nx = -dy
        ny = dx

        max_len = min(math.hypot(frame_w, frame_h) * 0.95, 900)
        tip = (
            int(wrist[0] + dx * max_len * self._progress),
            int(wrist[1] + dy * max_len * self._progress),
        )

        strand_count = max(4, self._cfg.WEB_STRAND_COUNT)
        ring_count = max(3, self._cfg.WEB_RING_COUNT)
        max_spread = self._cfg.WEB_MAX_RADIUS

        left_edge = []
        right_edge = []
        start = (int(wrist[0]), int(wrist[1]))

        # Thin bright centre strand.
        cv2.line(overlay, start, tip, self._cfg.WEB_COLOR_OUTER,
                 self._cfg.WEB_LINE_THICKNESS + 2, cv2.LINE_AA)
        cv2.line(overlay, start, tip, self._cfg.WEB_COLOR_INNER,
                 self._cfg.WEB_LINE_THICKNESS, cv2.LINE_AA)

        # Slim side strands and tiny cross webbing.
        for i in range(strand_count):
            t = (i + 1) / strand_count
            cx = wrist[0] + (tip[0] - wrist[0]) * t
            cy = wrist[1] + (tip[1] - wrist[1]) * t
            spread = math.sin(t * math.pi) * max_spread * (0.15 + 0.45 * t)

            left = (int(cx + nx * spread), int(cy + ny * spread))
            right = (int(cx - nx * spread), int(cy - ny * spread))
            left_edge.append(left)
            right_edge.append(right)

            cv2.line(overlay, start, left, self._cfg.WEB_COLOR_INNER, 1, cv2.LINE_AA)
            cv2.line(overlay, start, right, self._cfg.WEB_COLOR_INNER, 1, cv2.LINE_AA)

        for r_idx in range(1, ring_count + 1):
            idx = min(len(left_edge) - 1, int(r_idx * len(left_edge) / ring_count) - 1)
            if idx >= 0:
                cv2.line(overlay, left_edge[idx], right_edge[idx],
                         self._cfg.WEB_COLOR_INNER, 1, cv2.LINE_AA)

        cv2.circle(overlay, start, 4, (255, 255, 255), -1, cv2.LINE_AA)

    def reset(self):
        """Call when gesture is released so the next activation re-grows."""
        self._progress = 0.0
        self._was_active = False
