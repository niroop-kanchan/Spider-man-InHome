"""
core/hand_tracker.py
────────────────────
Wraps MediaPipe Hands so the rest of the project never imports mediapipe
directly — if you ever want to swap the tracking library you only change
this one file.

MediaPipe landmark index reference (21 points):
  0  WRIST
  1  THUMB_CMC      2  THUMB_MCP      3  THUMB_IP       4  THUMB_TIP
  5  INDEX_MCP      6  INDEX_PIP      7  INDEX_DIP      8  INDEX_TIP
  9  MIDDLE_MCP    10  MIDDLE_PIP    11  MIDDLE_DIP    12  MIDDLE_TIP
 13  RING_MCP      14  RING_PIP      15  RING_DIP      16  RING_TIP
 17  PINKY_MCP     18  PINKY_PIP     19  PINKY_DIP     20  PINKY_TIP
"""

import cv2
import mediapipe as mp
from utils.config import Config


class HandTracker:
    """
    Processes BGR frames and returns pixel-space (x, y) tuples for
    the detected hand's 21 landmarks.

    Only tracks the first detected hand (max_num_hands=1) for
    performance.  Extend to 2 if you later want dual-hand support.
    """

    # MediaPipe landmark indices — named for readability
    WRIST       = 0
    THUMB_TIP   = 4
    INDEX_MCP   = 5;  INDEX_TIP   = 8
    MIDDLE_MCP  = 9;  MIDDLE_TIP  = 12
    RING_MCP    = 13; RING_TIP    = 16
    PINKY_MCP   = 17; PINKY_TIP   = 20

    def __init__(self):
        cfg = Config()
        mp_hands = mp.solutions.hands
        self._hands = mp_hands.Hands(
            static_image_mode=False,          # video mode — faster
            max_num_hands=2,
            min_detection_confidence=cfg.DETECTION_CONFIDENCE,
            min_tracking_confidence=cfg.TRACKING_CONFIDENCE,
        )
        # Landmark drawing utility (used externally if needed)
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_hands = mp_hands

    # ── Public methods ────────────────────────────────────────────────────────

    def process(self, bgr_frame):
        """
        Run MediaPipe on one BGR frame.

        MediaPipe expects RGB, so we convert internally — the caller
        always works with BGR (OpenCV's native format).

        Returns the raw MediaPipe results object, or None on failure.
        """
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False          # micro-optimisation
        results = self._hands.process(rgb)
        rgb.flags.writeable = True
        return results

    def get_landmarks(self, results, frame_w: int, frame_h: int):
        """
        Extract pixel-space landmark coordinates from a MediaPipe result.

        MediaPipe returns normalised floats in [0, 1]; we multiply by the
        frame dimensions to get actual pixel positions.

        Parameters
        ----------
        results  : MediaPipe results object (from process())
        frame_w  : int — frame width  in pixels
        frame_h  : int — frame height in pixels

        Returns
        -------
        List of (x, y) int tuples, length 21 — one per landmark.
        Returns an empty list if no hand was detected.
        """
        all_hands = self.get_all_landmarks(results, frame_w, frame_h)
        return all_hands[0] if all_hands else []

    def get_all_landmarks(self, results, frame_w: int, frame_h: int):
        """Return one 21-point pixel landmark list for each detected hand."""
        if not results or not results.multi_hand_landmarks:
            return []

        return [
            [
                (int(lm.x * frame_w), int(lm.y * frame_h))
                for lm in hand.landmark
            ]
            for hand in results.multi_hand_landmarks
        ]

    def get_landmark_z(self, results):
        """
        Return the Z (depth) value for the wrist landmark.

        MediaPipe's Z is relative depth in the hand's reference frame —
        not real-world metres.  Negative Z = hand closer to camera.
        Returns 0.0 if no hand is detected.
        """
        if not results or not results.multi_hand_landmarks:
            return 0.0
        return results.multi_hand_landmarks[0].landmark[self.WRIST].z
