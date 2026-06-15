"""
core/gesture_detector.py
────────────────────────
Detects the Spider-Man "web-shooting" gesture using the 21 MediaPipe
hand landmarks.

The Gesture
───────────
  ✔  Index finger  — EXTENDED  (pointing out)
  ✔  Pinky finger  — EXTENDED  (pointing out)
  ✗  Middle finger — FOLDED    (curled in)
  ✗  Ring finger   — FOLDED    (curled in)
  ✔  Thumb         — roughly extended sideways (optional check)

How "extended" is determined
─────────────────────────────
For each finger we compare the TIP landmark with the MCP (knuckle)
landmark.  If the tip is further from the wrist than the MCP, the
finger is considered extended.  This simple rule works reliably across
hand sizes and distances because it is scale-independent.

A debounce counter prevents single-frame noise from toggling the state.
"""

from utils.config import Config


class GestureDetector:
    """Stateful gesture detector — call is_web_gesture() every frame."""

    # MediaPipe landmark indices (duplicated here for self-contained reading)
    WRIST = 0
    THUMB_CMC = 1; THUMB_TIP = 4
    INDEX_MCP = 5; INDEX_TIP = 8
    MIDDLE_MCP = 9; MIDDLE_TIP = 12
    RING_MCP = 13; RING_TIP = 16
    PINKY_MCP = 17; PINKY_TIP = 20

    def __init__(self):
        cfg = Config()
        self._hold_threshold = cfg.GESTURE_HOLD_FRAMES
        self._hold_counter = 0      # frames the gesture has been held
        self._active = False        # current debounced state

    # ── Public API ────────────────────────────────────────────────────────────

    def is_web_gesture(self, landmarks: list) -> bool:
        """
        Return True if the web-shooting gesture is currently held.

        Parameters
        ----------
        landmarks : list of (x, y) int tuples, length 21
        """
        if len(landmarks) < 21:
            self._reset()
            return False

        raw = self._detect_raw(landmarks)

        # Debounce: require GESTURE_HOLD_FRAMES consecutive positive frames
        if raw:
            self._hold_counter = min(self._hold_counter + 1, self._hold_threshold)
        else:
            self._hold_counter = max(self._hold_counter - 1, 0)

        # Hysteresis: activate at threshold, deactivate at 0
        if self._hold_counter >= self._hold_threshold:
            self._active = True
        elif self._hold_counter == 0:
            self._active = False

        return self._active

    def get_finger_states(self, landmarks: list) -> list:
        """
        Return a list of five booleans [thumb, index, middle, ring, pinky]
        indicating which fingers are currently extended.
        Used by the debug overlay.
        """
        if len(landmarks) < 21:
            return [False] * 5

        wrist = landmarks[self.WRIST]
        return [
            self._is_extended(landmarks, wrist, self.THUMB_CMC,  self.THUMB_TIP),
            self._is_extended(landmarks, wrist, self.INDEX_MCP,  self.INDEX_TIP),
            self._is_extended(landmarks, wrist, self.MIDDLE_MCP, self.MIDDLE_TIP),
            self._is_extended(landmarks, wrist, self.RING_MCP,   self.RING_TIP),
            self._is_extended(landmarks, wrist, self.PINKY_MCP,  self.PINKY_TIP),
        ]

    # ── Private helpers ───────────────────────────────────────────────────────

    def _detect_raw(self, landmarks: list) -> bool:
        """
        Raw (non-debounced) gesture check.

        Returns True only when:
          • Index  is extended
          • Pinky  is extended
          • Middle is folded
          • Ring   is folded
        The thumb check is intentionally relaxed — people hold it
        differently and it would cause too many false negatives.
        """
        wrist = landmarks[self.WRIST]

        index_up  = self._is_extended(landmarks, wrist, self.INDEX_MCP,  self.INDEX_TIP)
        middle_up = self._is_extended(landmarks, wrist, self.MIDDLE_MCP, self.MIDDLE_TIP)
        ring_up   = self._is_extended(landmarks, wrist, self.RING_MCP,   self.RING_TIP)
        pinky_up  = self._is_extended(landmarks, wrist, self.PINKY_MCP,  self.PINKY_TIP)

        # Be forgiving: camera angle often makes either middle or ring look
        # partly extended for one frame. Index + pinky must be up, and at
        # least one of the two centre fingers must still look folded.
        return index_up and pinky_up and ((not middle_up) or (not ring_up))

    @staticmethod
    def _is_extended(landmarks, wrist, mcp_idx: int, tip_idx: int) -> bool:
        """
        A finger is "extended" when its TIP is further from the WRIST
        than its MCP (base knuckle).

        dist² comparison avoids a sqrt — faster and just as correct.
        """
        def dist2(a, b):
            return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

        tip_dist = dist2(landmarks[tip_idx], wrist)
        mcp_dist = dist2(landmarks[mcp_idx], wrist)
        return tip_dist > mcp_dist * 1.02  # small buffer to avoid edge flicker

    def _reset(self):
        self._hold_counter = 0
        self._active = False
