#!/usr/bin/env python3
"""Minimal usage example for napari-in-subprocess.

Simulates an acquisition loop: it generates synthetic frames and streams them
to a non-blocking napari window via the public API (display -> show_image),
then closes the viewer.

    python example.py

The main process never blocks on napari -- in real code your camera/acquisition
work would run here, calling show_image() whenever a new frame is ready.

NOTE: the work must live under `if __name__ == '__main__':`. On Windows the
napari child process is started with the 'spawn' method, which re-imports this
module; guarding the entry point prevents it from re-running in the child.
"""
import time

import numpy as np

from concurrency_tools import SharedNDArray
from napari_in_subprocess import display


def fill_frame(buf, t):
    """Write a moving 2-D Gaussian blob into `buf` (in place)."""
    h, w = buf.shape
    ys, xs = np.mgrid[0:h, 0:w]
    cy = h * (0.5 + 0.3 * np.sin(t))          # blob drifts in a circle
    cx = w * (0.5 + 0.3 * np.cos(t))
    sigma = 0.12 * min(h, w)
    blob = np.exp(-((ys - cy) ** 2 + (xs - cx) ** 2) / (2 * sigma ** 2))
    buf[:] = (blob * 60000).astype("uint16")


if __name__ == "__main__":
    H, W = 1024, 1024
    n_frames = 200

    # One reusable shared-memory buffer, passed to the viewer each frame.
    frame = SharedNDArray(shape=(H, W), dtype="uint16")

    viewer = display()                     # launches napari in a child process
    print(f"Streaming {n_frames} frames to napari... (Ctrl+C to stop early)")
    try:
        for i in range(n_frames):
            fill_frame(frame, t=i / 15)    # <- your camera.snap(out=frame) goes here
            viewer.show_image(frame)       # non-blocking canvas update
            time.sleep(1 / 30)             # ~30 fps
    except KeyboardInterrupt:
        pass

    input("Done streaming. Press Enter to close the viewer... ")
    viewer.close()
