"""
utils/config.py
───────────────
Central configuration object.  Tweak these values to personalise the
experience without hunting through source files.
"""


class Config:
    # ── Camera ────────────────────────────────────────────────────────────────
    CAMERA_INDEX: int = 0          # 0 = default webcam; try 1 or 2 for USB cams
    FRAME_WIDTH:  int = 1280       # Requested capture width  (may be capped by cam)
    FRAME_HEIGHT: int = 720        # Requested capture height

    # ── Gesture ───────────────────────────────────────────────────────────────
    # Confidence thresholds for MediaPipe hand detection/tracking
    DETECTION_CONFIDENCE:  float = 0.55
    TRACKING_CONFIDENCE:   float = 0.55

    # How many consecutive frames the gesture must be held before it
    # "activates" — prevents accidental single-frame triggers.
    GESTURE_HOLD_FRAMES: int = 1

    # ── Zoom ──────────────────────────────────────────────────────────────────
    MAX_ZOOM:          float = 1.5   # Maximum zoom multiplier (1.5 = 150 %)
    ZOOM_SPEED:        float = 0.18  # How quickly zoom increases per frame
    ZOOM_RELEASE_SPEED:float = 0.08  # How quickly zoom resets after gesture ends
    # Fraction of frame height the wrist must rise to count as a "pull"
    PULL_THRESHOLD:    float = 0.05

    # ── Motion blur ───────────────────────────────────────────────────────────
    BLUR_MAX_KERNEL:   int   = 25    # Maximum blur kernel size (odd number)
    BLUR_DIRECTION_ANGLE: float = 0  # 0 = horizontal streaks; 90 = vertical

    # ── Web rendering ─────────────────────────────────────────────────────────
    WEB_COLOR_INNER: tuple = (255, 255, 255)   # BGR — bright movie-style white
    WEB_COLOR_OUTER: tuple = (190, 215, 255)   # BGR — soft white-blue glow
    WEB_LINE_THICKNESS: int = 1
    WEB_STRAND_COUNT:   int = 7      # Number of side strands on the web beam
    WEB_RING_COUNT:     int = 4      # Number of cross strands
    WEB_MAX_RADIUS:     int = 70     # Slim perspective spread around the beam
    WEB_GROW_SPEED:     float = 0.35 # How fast the web shoots out (0–1)

    # ── Camera shake (optional) ───────────────────────────────────────────────
    SHAKE_ENABLED:     bool  = False
    SHAKE_MAGNITUDE:   int   = 6     # Max pixel offset during shake
    SHAKE_DECAY:       float = 0.85  # How quickly the shake dies down (< 1)
