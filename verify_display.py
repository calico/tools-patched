#!/usr/bin/env python3
"""Visual smoke-test for napari-in-subprocess.

Run this on a new machine to confirm the non-blocking napari viewer renders
images correctly (a proper rectangle -- not a triangle or a black canvas):

    python verify_display.py

A napari window should open showing a CHECKERBOARD with a bright border on all
four sides and a solid rectangle in the upper-left. If instead you see a
triangle or a black canvas, a Qt6 binding is missing or not selected -- see
README.md ("Troubleshooting").
"""
import importlib.util
import time

import numpy as np

from concurrency_tools import SharedNDArray
from napari_in_subprocess import display


def report_qt_bindings():
    """Print which Qt6 bindings are available (helps diagnose deployments)."""
    have = [name for name in ("PySide6", "PyQt6")
            if importlib.util.find_spec(name) is not None]
    if have:
        print("Qt6 binding(s) available:", ", ".join(have))
    else:
        print("WARNING: no Qt6 binding (PySide6 / PyQt6) found -- the canvas "
              "will likely be broken.\n         Fix it with:  pip install PySide6")


def make_pattern(shift=0):
    """A structured pattern that makes any shear/corruption obvious."""
    H, W = 1024, 1200
    buf = SharedNDArray(shape=(H, W), dtype="uint16")
    ys, xs = np.mgrid[0:H, 0:W]
    buf[:] = 0
    buf[(((ys + shift) // 96 + (xs + shift) // 96) % 2) == 1] = 40000  # checkerboard
    buf[:12, :] = 65000                                                # borders
    buf[-12:, :] = 65000
    buf[:, :12] = 65000
    buf[:, -12:] = 65000
    buf[120:360, 180:560] = 20000                                      # solid rectangle
    return buf


if __name__ == "__main__":
    report_qt_bindings()
    print("Opening non-blocking napari viewer via display()...")
    viewer = display()
    viewer.show_image(make_pattern())
    print(
        "\nYou should now see a CHECKERBOARD with a bright border on all four\n"
        "sides and a solid rectangle. That means rendering works correctly.\n"
        "A triangle or a black canvas means the fix is not active (see README).\n"
    )
    try:
        input("Press Enter here to close the viewer and exit... ")
    except EOFError:
        # No interactive stdin (e.g. launched headless): just wait a bit.
        time.sleep(20)
    viewer.close()
    print("Done.")
