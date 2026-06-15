"""
SpiderVision: Real-Time AR Web Swing Simulator
=============================================
Main entry point. Run this file to start the app:
    python main.py

Controls:
    Q or ESC  - Quit the application
    D         - Toggle debug overlay (shows landmarks)
    S         - Save a screenshot
"""

import cv2
import sys
import os
import math

# Make sure local packages are importable when run from any directory
sys.path.insert(0, os.path.dirname(__file__))

from core.camera import Camera
from core.hand_tracker import HandTracker
from core.gesture_detector import GestureDetector
from core.zoom_controller import ZoomController
from effects.web_renderer import WebRenderer
from effects.motion_blur import MotionBlur
from utils.fps_counter import FPSCounter
from utils.config import Config


def main():
    """Application entry point — wires all modules together and runs the main loop."""

    cfg = Config()                          # Central config/settings object
    cap = Camera(cfg.CAMERA_INDEX)          # Webcam wrapper
    tracker = HandTracker()                 # MediaPipe hand-tracking wrapper
    gestures = [GestureDetector(), GestureDetector()]  # One debounce state per hand
    zoom = ZoomController(cfg)              # Pull-to-zoom controller
    web = WebRenderer(cfg)                  # Web animation renderer
    blur = MotionBlur()                     # Motion-blur effect
    fps = FPSCounter()                      # On-screen FPS display

    debug_mode = False                      # Toggle with D key

    print("SpiderVision started. Press Q or ESC to quit, D to toggle debug.")

    while True:
        # ── 1. Capture frame ────────────────────────────────────────────────
        ret, frame = cap.read()
        if not ret:
            print("Camera feed lost — exiting.")
            break

        # Flip horizontally so the display acts like a mirror
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        # ── 2. Hand tracking ─────────────────────────────────────────────────
        results = tracker.process(frame)
        hands_landmarks = tracker.get_all_landmarks(results, w, h)

        # ── 3. Gesture detection ─────────────────────────────────────────────
        web_active = False
        active_hands = []
        active_wrists = []
        active_scales = []
        zoom_wrist = None
        zoom_scale = 0.0

        for hand_idx, landmarks in enumerate(hands_landmarks[:2]):
            if gestures[hand_idx].is_web_gesture(landmarks):
                active_hands.append(landmarks)
                active_wrists.append(landmarks[0])   # Landmark 0 is the wrist
                active_scales.append(_hand_scale(landmarks))

        web_active = bool(active_wrists)
        if active_wrists:
            zoom_wrist = (
                int(sum(pos[0] for pos in active_wrists) / len(active_wrists)),
                int(sum(pos[1] for pos in active_wrists) / len(active_wrists)),
            )
            zoom_scale = sum(active_scales) / len(active_scales)

        zoom.update(web_active, zoom_wrist if zoom_wrist else (0, 0), h, zoom_scale)

        # ── 4. Apply zoom ────────────────────────────────────────────────────
        frame = zoom.apply(frame)

        # ── 5. Apply motion blur (only during active zoom) ───────────────────
        if zoom.is_zooming():
            frame = blur.apply(frame, zoom.zoom_velocity())

        # ── 6. Draw web animation ────────────────────────────────────────────
        if web_active:
            frame = web.draw_many(frame, active_hands, w, h)
        else:
            web.reset()

        # ── 7. Debug overlay — landmarks + finger states ─────────────────────
        if debug_mode and hands_landmarks:
            for hand_idx, landmarks in enumerate(hands_landmarks[:2]):
                frame = _draw_debug(frame, landmarks, gestures[hand_idx])

        # ── 8. HUD (FPS + status text) ───────────────────────────────────────
        fps.update()
        frame = _draw_hud(frame, fps.get(), web_active, zoom.get_zoom_level(), w, h)

        # ── 9. Show ──────────────────────────────────────────────────────────
        cv2.imshow("SpiderVision", frame)

        # ── 10. Key handling ─────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), 27):          # Q or ESC
            break
        elif key == ord('d'):
            debug_mode = not debug_mode
            print(f"Debug mode: {'ON' if debug_mode else 'OFF'}")
        elif key == ord('s'):
            fname = f"screenshot_{fps.frame_count}.png"
            cv2.imwrite(fname, frame)
            print(f"Screenshot saved: {fname}")

    # ── Cleanup ──────────────────────────────────────────────────────────────
    cap.release()
    cv2.destroyAllWindows()
    print("SpiderVision closed.")


# ─────────────────────────────────────────────────────────────────────────────
# Helper: debug overlay
# ─────────────────────────────────────────────────────────────────────────────

def _draw_debug(frame, landmarks, gesture: GestureDetector):
    """
    Draws every hand landmark as a small circle and prints which
    fingers are currently extended.  Only shown when debug_mode is True.
    """
    # Draw all 21 landmarks
    for i, (lx, ly) in enumerate(landmarks):
        cv2.circle(frame, (lx, ly), 4, (0, 255, 255), -1)
        cv2.putText(frame, str(i), (lx + 5, ly - 5),
                    cv2.FONT_HERSHEY_PLAIN, 0.7, (0, 255, 255), 1)

    # Finger extension states
    states = gesture.get_finger_states(landmarks)
    labels = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
    for i, (label, state) in enumerate(zip(labels, states)):
        color = (0, 255, 0) if state else (0, 0, 255)
        text = f"{label}: {'UP' if state else 'DOWN'}"
        cv2.putText(frame, text, (10, 120 + i * 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1, cv2.LINE_AA)
    return frame


# ─────────────────────────────────────────────────────────────────────────────
# Helper: HUD
# ─────────────────────────────────────────────────────────────────────────────

def _hand_scale(landmarks):
    """
    Estimate hand size from stable palm landmarks. The zoom controller uses
    this to detect a pull toward the camera, where the hand appears larger.
    """
    wrist = landmarks[0]
    index_mcp = landmarks[5]
    middle_mcp = landmarks[9]
    pinky_mcp = landmarks[17]

    return (
        math.dist(wrist, index_mcp)
        + math.dist(wrist, middle_mcp)
        + math.dist(wrist, pinky_mcp)
    ) / 3.0


def _draw_hud(frame, fps_val, web_active, zoom_level, w, h):
    """
    Draws the always-visible heads-up display:
      - FPS counter (top-left)
      - Web status (top-right, glows red when active)
      - Zoom percentage (bottom-left)
    """
    # FPS
    cv2.putText(frame, f"FPS: {fps_val:.0f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2, cv2.LINE_AA)

    # Web status
    if web_active:
        status_text = "WEB ACTIVATED"
        status_color = (0, 60, 220)    # Vivid red in BGR
        # Pulsing background rectangle
        cv2.rectangle(frame, (w - 210, 8), (w - 8, 42), (0, 0, 180), -1)
        cv2.rectangle(frame, (w - 210, 8), (w - 8, 42), (0, 60, 255),  2)
    else:
        status_text = "No gesture"
        status_color = (120, 120, 120)

    cv2.putText(frame, status_text, (w - 205, 32),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255) if web_active else status_color,
                2 if web_active else 1, cv2.LINE_AA)

    # Zoom level
    zoom_pct = int(zoom_level * 100)
    cv2.putText(frame, f"Zoom: {zoom_pct}%", (10, h - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA)

    return frame


if __name__ == "__main__":
    main()
