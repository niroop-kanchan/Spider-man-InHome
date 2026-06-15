"""
core/camera.py
──────────────
Thin wrapper around cv2.VideoCapture that:
  • Opens the camera at startup and raises a clear error if it fails.
  • Sets resolution to the values in Config (best-effort — the driver may
    cap them at its maximum supported size).
  • Exposes the same read() / release() interface as raw VideoCapture so
    the rest of the code doesn't need to know this class exists.
"""

import cv2
from utils.config import Config


class Camera:
    """
    Parameters
    ----------
    index : int
        Camera index passed to cv2.VideoCapture.
        0 = built-in webcam on most laptops.
        1, 2, … = additional USB cameras.
    """

    def __init__(self, index: int = 0):
        self._cap = cv2.VideoCapture(index)

        if not self._cap.isOpened():
            raise RuntimeError(
                f"Could not open camera at index {index}. "
                "Check that no other app is using it and that the index is correct "
                "(try 0, 1, or 2)."
            )

        # Request preferred resolution — the driver will choose the closest
        # supported mode, so actual resolution may differ.
        cfg = Config()
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  cfg.FRAME_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.FRAME_HEIGHT)

        # Report what we actually got
        actual_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"Camera opened at {actual_w}×{actual_h}")

    # ── Public interface ──────────────────────────────────────────────────────

    def read(self):
        """
        Grab and decode the next frame.

        Returns
        -------
        ret   : bool   – True if a frame was successfully captured.
        frame : ndarray – BGR image array, or None on failure.
        """
        return self._cap.read()

    def release(self):
        """Release the camera so other apps can use it."""
        self._cap.release()

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def width(self) -> int:
        return int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    @property
    def height(self) -> int:
        return int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
