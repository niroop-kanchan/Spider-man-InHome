# SpiderVision 🕷️
### Real-Time AR Web Swing Simulator

A desktop Python app that uses your webcam and MediaPipe hand-tracking to
detect the Spider-Man web-shooting gesture and overlay an animated web — with
a pull-to-zoom effect that makes it feel like you're swinging through the city.

---

## Table of Contents

1. [Project Architecture](#1-project-architecture)
2. [Folder Structure](#2-folder-structure)
3. [Installation Guide](#3-installation-guide)
4. [Step-by-Step Implementation Plan](#4-step-by-step-implementation-plan)
5. [File-by-File Explanation](#5-file-by-file-explanation)
6. [Key Functions Explained](#6-key-functions-explained)
7. [Common Bugs & Fixes](#7-common-bugs--fixes)
8. [Performance Optimisation Tips](#8-performance-optimisation-tips)
9. [Future Upgrades](#9-future-upgrades)

---

## 1. Project Architecture

```
User webcam
    │
    ▼
Camera (core/camera.py)          ← captures BGR frames
    │
    ▼
HandTracker (core/hand_tracker.py) ← MediaPipe → 21 (x,y) landmarks
    │
    ├──► GestureDetector (core/gesture_detector.py)
    │         └── is_web_gesture()  ← True / False
    │
    ├──► ZoomController (core/zoom_controller.py)
    │         ├── update()          ← advances zoom state
    │         └── apply(frame)      ← crops + resizes frame
    │
    ├──► WebRenderer (effects/web_renderer.py)
    │         └── draw(frame, wrist) ← paints animated web
    │
    └──► MotionBlur (effects/motion_blur.py)
              └── apply(frame, vel) ← streaks during fast zoom

All wired together in main.py.
Config values live in utils/config.py — edit there, not in source files.
```

---

## 2. Folder Structure

```
SpiderVision/
├── main.py                   # Entry point — run this
├── requirements.txt          # pip dependencies
├── README.md                 # This file
│
├── core/                     # Computer-vision logic
│   ├── __init__.py
│   ├── camera.py             # Webcam wrapper
│   ├── hand_tracker.py       # MediaPipe wrapper
│   ├── gesture_detector.py   # Spider-Man gesture logic
│   └── zoom_controller.py    # Pull-to-zoom + camera shake
│
├── effects/                  # Visual effects
│   ├── __init__.py
│   ├── web_renderer.py       # Animated web overlay
│   └── motion_blur.py        # Directional blur during zoom
│
└── utils/                    # Helpers
    ├── __init__.py
    ├── config.py             # All tunable constants
    └── fps_counter.py        # Rolling-average FPS display
```

---

## 3. Installation Guide

### Prerequisites
| Requirement | Notes |
|---|---|
| Python 3.11 or newer | `python --version` to check |
| pip | bundled with Python |
| A webcam | built-in or USB |

### Step 1 — Clone / download the project

```bash
# If you have git:
git clone https://github.com/yourname/SpiderVision.git
cd SpiderVision

# Or just unzip the folder and cd into it.
```

### Step 2 — Create a virtual environment (strongly recommended)

```bash
python -m venv venv

# Activate it:
# macOS / Linux:
source venv/bin/activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (cmd):
venv\Scripts\activate.bat
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

This installs:
- **opencv-python** — webcam capture and image processing
- **mediapipe** — real-time hand landmark detection
- **numpy** — fast array maths

### Step 4 — Run the app

```bash
python main.py
```

A window called *SpiderVision* should open showing your webcam feed.

---

## 4. Step-by-Step Implementation Plan

The project was built in five incremental stages.  If you want to learn by
building it yourself, follow this order:

### Stage 1 — Webcam Setup
- Create `core/camera.py` with `cv2.VideoCapture`
- Write a minimal `main.py` that opens the camera and shows frames
- Confirm you see a live mirror image

### Stage 2 — Hand Tracking
- Create `core/hand_tracker.py` wrapping `mediapipe.solutions.hands`
- Call `tracker.process(frame)` and `tracker.get_landmarks(results, w, h)`
- In `main.py`, draw circles at each of the 21 landmarks to verify tracking

### Stage 3 — Gesture Detection
- Create `core/gesture_detector.py`
- Implement `_is_extended()` using wrist→MCP vs wrist→TIP distance
- Add the debounce counter in `is_web_gesture()`
- Print "WEB!" to the console when the gesture fires — confirm reliability

### Stage 4 — Web Animation
- Create `effects/web_renderer.py`
- Draw strands with `cv2.line` in a radial pattern from the wrist
- Add concentric rings connecting the strand endpoints
- Implement the `_progress` variable so the web grows in over ~8 frames
- Alpha-blend the overlay: `cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0, dst)`

### Stage 5 — Pull-to-Zoom
- Create `core/zoom_controller.py`
- Record `_ref_y` on the first active frame
- Compute `pull_norm` from wrist Y movement
- Use `lerp()` to smoothly move `_current_zoom` toward `_target_zoom`
- Crop the frame centre by `1/zoom` and resize back to original dimensions
- Add `effects/motion_blur.py` for the rush effect
- Optionally add camera shake

---

## 5. File-by-File Explanation

### `main.py`
The application loop.  Each iteration:
1. Reads a frame from the camera and flips it (mirror mode).
2. Runs MediaPipe hand tracking.
3. Asks the gesture detector if the web gesture is active.
4. Updates the zoom controller with the current wrist position.
5. Applies zoom to the frame.
6. Applies motion blur if zoom is active.
7. Draws the web overlay.
8. Draws the HUD (FPS, status, zoom %).
9. Shows the frame and handles keyboard input.

### `utils/config.py`
A plain Python class with class-level constants.  No logic — just numbers
and colours.  Edit this file to tune the experience without touching any
algorithm.

### `utils/fps_counter.py`
Maintains a `deque` of recent frame-times.  `get()` returns the average
FPS over the last `window` frames.

### `core/camera.py`
Wraps `cv2.VideoCapture`.  Raises a clear error on failure.  Sets
resolution at startup.  Exposes `read()` and `release()`.

### `core/hand_tracker.py`
Wraps `mediapipe.solutions.hands`.  Key responsibility: converting
MediaPipe's normalised [0, 1] landmark coordinates into pixel positions.

### `core/gesture_detector.py`
Implements the web-gesture check:
- **Extended** = TIP further from wrist than MCP × 1.1 buffer
- **Gesture** = index UP, pinky UP, middle DOWN, ring DOWN
- **Debounce** = must hold for `GESTURE_HOLD_FRAMES` consecutive frames

### `core/zoom_controller.py`
On each frame, calculates how far the wrist has risen since activation,
maps that to a target zoom, and lerps the current zoom toward the target.
Applies zoom by cropping the frame centre and upscaling.

### `effects/web_renderer.py`
Draws radial strands and concentric rings on a copy of the frame, then
alpha-blends that copy back onto the original.  The `_progress` variable
controls how far the web has grown (0 = hidden, 1 = full size).

### `effects/motion_blur.py`
Builds a directional convolution kernel and applies it with `cv2.filter2D`.
Kernel size scales with zoom velocity so fast-zoom = heavy blur.

---

## 6. Key Functions Explained

### `GestureDetector._is_extended(landmarks, wrist, mcp_idx, tip_idx)`
```python
def dist2(a, b):
    return (a[0]-b[0])**2 + (a[1]-b[1])**2

tip_dist = dist2(landmarks[tip_idx], wrist)
mcp_dist = dist2(landmarks[mcp_idx], wrist)
return tip_dist > mcp_dist * 1.1
```
Uses squared Euclidean distance (no sqrt → faster).  The 1.1 multiplier
adds a 10 % buffer so a finger right at the boundary doesn't flicker.

### `ZoomController.apply(frame)`
```python
cw = w / z          # crop width shrinks as zoom grows
ch = h / z
x1 = int(cx - cw/2);  x2 = int(cx + cw/2)
y1 = int(cy - ch/2);  y2 = int(cy + ch/2)
cropped = frame[y1:y2, x1:x2]
return cv2.resize(cropped, (w, h))
```
At zoom 2×: crop is 50 % of the frame, then upscaled 2× → objects appear
twice as large.  The crop is centred on the frame + shake offset.

### `MotionBlur._make_kernel(size, angle_deg)`
Iterates over integer steps along a line at `angle_deg`.  Each integer
step lights up one cell of the kernel matrix.  The result is normalised
so total weight = 1 (brightness is preserved).

### `WebRenderer.draw(frame, wrist_pos, w, h)`
1. Advance `_progress` by `WEB_GROW_SPEED`.
2. Compute strand endpoints at `max_radius * progress` distance.
3. Draw strands and rings onto `overlay = frame.copy()`.
4. `cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)` blends.

---

## 7. Common Bugs & Fixes

| Symptom | Cause | Fix |
|---|---|---|
| Black screen / camera error | Wrong camera index | Change `CAMERA_INDEX` in `config.py` to 1 or 2 |
| Gesture fires randomly | Lighting too dark or bright | Add a lamp facing you; avoid back-lighting |
| Gesture never fires | Detection confidence too high | Lower `DETECTION_CONFIDENCE` to 0.6 |
| Web position is mirrored wrong | Forgot to flip frame | `frame = cv2.flip(frame, 1)` must happen before tracking |
| Very low FPS | Resolution too high | Set `FRAME_WIDTH = 640`, `FRAME_HEIGHT = 480` in config |
| `ModuleNotFoundError: mediapipe` | Not installed | Run `pip install -r requirements.txt` inside the venv |
| Zoom never activates | Wrist not rising enough | Lower `PULL_THRESHOLD` from 0.08 to 0.05 |
| Zoom jumps suddenly | Lerp speed too high | Lower `ZOOM_SPEED` to 0.02 |
| Web flickers on/off | No debounce or too short | Increase `GESTURE_HOLD_FRAMES` to 5 |
| `cv2.imshow` crash on macOS | macOS + OpenCV threading | Run `python main.py` from a Terminal (not an IDE) |

---

## 8. Performance Optimisation Tips

1. **Lower resolution first** — Drop to 640×480 in config.  Most effects
   are imperceptible at this size and FPS doubles.

2. **Limit MediaPipe complexity** — MediaPipe Hands has a `model_complexity`
   parameter (0, 1, 2).  The default is 1; use 0 for maximum speed.
   ```python
   mp_hands.Hands(model_complexity=0, ...)
   ```

3. **Skip frames** — If FPS is still low, run hand tracking every other
   frame and reuse the last landmarks on skipped frames.

4. **Use INTER_NEAREST for resize** — Replace `cv2.INTER_LINEAR` with
   `cv2.INTER_NEAREST` in `zoom_controller.py` for a small speedup at
   the cost of slightly rougher zoom.

5. **Avoid Python loops in hot paths** — `web_renderer.py` uses a Python
   `for` loop to draw strands.  For very high strand counts, pre-compute
   the endpoint arrays and use `cv2.polylines` with a NumPy array.

6. **Profile first** — Add `import cProfile; cProfile.run('main()')` to
   find the real bottleneck before optimising blind.

---

## 9. Future Upgrades

The codebase is intentionally modular so these can be added without
rewriting existing code.

### Multiple Web Shots
- In `WebRenderer`, maintain a list of `WebInstance` objects (each with
  its own `_progress` and `wrist_pos`).
- Add a second gesture (e.g. other hand, or a double-tap trigger).

### AR Targets
- Add a `target_manager.py` in `core/` that places 2-D targets at fixed
  screen positions.
- Detect when the web's outer ring intersects a target's bounding box.

### Voice Command ("Fire Web")
- Integrate `SpeechRecognition` + `pyaudio` in a background thread.
- Post a `VOICE_TRIGGER` event to the main loop via `queue.Queue`.

### Sound Effects
- Use `pygame.mixer` or `playsound`.
- Trigger `web_shoot.wav` on gesture activation and `zoom.wav` on pull.

### Web-Swing Physics
- Track wrist position over ~30 frames to compute velocity vector.
- Animate a separate overlay showing the arc of swing.

### Unity Integration
- Output gesture state + zoom level over a UDP socket each frame.
- In Unity, read with a C# `UdpClient` and drive a character controller.

### AI Gesture Customisation
- Record positive/negative frames for any gesture.
- Train a small `sklearn` or `TFLite` classifier on landmark coordinates.
- Swap out `GestureDetector` with the trained model — no code refactor needed.

---

*Built with ♥ using Python, OpenCV, and MediaPipe.*
