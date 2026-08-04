# napari-in-subprocess

A small, deploy-anywhere **non-blocking [napari](https://napari.org) viewer**
that runs in its own process — built for live microscopy / instrument-control
code. Push image frames to a napari window straight from your acquisition loop
without blocking it, using shared-memory arrays for fast, copy-free transfer.

This wraps two modules from the [AndrewGYork lab tools](https://github.com/AndrewGYork/tools),
patched to fix a canvas-corruption bug triggered by recent NVIDIA drivers — see
[The bug and the fix](#the-bug-and-the-fix).

## Why

`napari.Viewer()` runs a **blocking** Qt event loop, which fights with an
acquisition loop. This package runs napari in a **child process** and exposes a
tiny API (`display()`, `show_image()`, `close()`) so your main process stays
responsive. Large frames are shared via `SharedNDArray` (backed by
`multiprocessing.shared_memory`), so there's no per-frame serialization cost.

## Requirements

- Python 3.9+
- `numpy`
- `napari` (tested on 0.4.19 **and** 0.8.0)
- **A Qt6 binding: `PySide6` or `PyQt6`** ← important, see below

> ⚠️ **Use a Qt6 binding.** The old Qt5 bindings (`PyQt5`, `PySide2`) cause a
> corrupt/triangular or black canvas on recent NVIDIA drivers. This package
> automatically selects PySide6 (then PyQt6) for the napari subprocess, but one
> of them must be installed.

## Install / deploy

Copy `napari_in_subprocess.py` and `concurrency_tools.py` into your project (or
clone this repo), then make sure a Qt6 binding is present.

On a machine that **already has a working napari environment**, you usually only
need to add the Qt6 binding — this avoids upgrading napari/numpy unintentionally:

```bash
pip install PySide6
```

For a **fresh environment**:

```bash
pip install -r requirements.txt
```

## Usage

```python
import numpy as np
from concurrency_tools import SharedNDArray
from napari_in_subprocess import display

viewer = display()                 # launches napari in a child process

frame = SharedNDArray(shape=(2048, 2048), dtype='uint16')
frame[:] = camera.snap()           # fill the shared buffer
viewer.show_image(frame)           # non-blocking; updates the napari canvas

# ... acquisition loop: refill `frame` and call show_image() again ...

viewer.close()                     # close the viewer window
```

`show_image()` adds the image on the first call and updates it **in place** on
later calls. To customize the viewer, subclass `_NapariDisplay` and pass it:
`display(MyDisplay)`. The only requirement for a custom class is a `close`
method.

See the `if __name__ == '__main__'` block in `napari_in_subprocess.py` for a
fuller mock-microscope example (camera + display running across processes).

## Verify it works

```bash
python verify_display.py
```

A napari window should show a **checkerboard with a bright border on all four
sides and a solid rectangle**. That means rendering works. If you instead see a
**triangle** or a **black canvas**, your Qt6 binding is missing or not selected
— see [Troubleshooting](#troubleshooting).

## The bug and the fix

**Symptom:** after a Windows/driver update, images that used to display as
rectangles rendered as a corrupt **triangle** (or a black canvas).

**Root cause:** it was **not** napari, vispy, or the image data — it was the
**Qt5 binding**. A recent **NVIDIA driver (595.95)** has broken OpenGL behavior
when napari/vispy render through PyQt5. Verified on that driver:

| napari  | Qt binding     | Result       |
| ------- | -------------- | ------------ |
| 0.4.19  | PyQt5          | 🔺 triangle  |
| 0.8.0   | PyQt5          | ⬛ black      |
| 0.4.19  | PySide6        | ✅ correct    |
| 0.8.0   | PySide6 / PyQt6| ✅ correct    |

(The napari GUI and the CPU-drawn layer thumbnail always rendered correctly —
only the GPU canvas was affected — which is how the data path was ruled out.)

**Fix** (all in `napari_in_subprocess.py`):

1. **Select a Qt6 binding** (`PySide6`, else `PyQt6`) via `QT_API`, set *inside
   the napari child process only* — so the parent application's Qt is never
   touched.
2. **Replaced `napari.gui_qt()`** (removed in napari 0.5) **with
   `napari.run()`**, so the file works on napari 0.4.19 through 0.8+.
3. **Deferred the `napari` / `qtpy` imports** out of module-import time into the
   child process, so importing this module in your main process loads neither
   napari nor qtpy and cannot disturb your app's own Qt binding.

The public API (`display`, `_NapariDisplay`, `show_image`, `close`) is
unchanged and `concurrency_tools.py` is untouched, so existing code keeps
working without modification.

## Troubleshooting

- **Triangle / black canvas:** No Qt6 binding is installed, or a Qt5 one is
  being forced. Run `pip install PySide6`, and make sure nothing sets
  `QT_API=pyqt5` in the environment that launches the subprocess.
- **`ImportError` about qtpy / Qt:** Install `PySide6` (or `PyQt6`).
- **Window never appears / hangs:** Don't call `display()` at import time in a
  module that the child re-imports (Windows uses the `spawn` start method). Call
  it from inside `if __name__ == '__main__':` or from a function.

## Files

- `napari_in_subprocess.py` — the non-blocking napari viewer (patched).
- `concurrency_tools.py` — subprocess/threading/shared-memory helpers
  (`ObjectInSubprocess`, `SharedNDArray`, `CustodyThread`, …), unmodified upstream.
- `verify_display.py` — visual smoke-test.
- `example.py` — minimal streaming example (simulated acquisition loop).
- `requirements.txt` — dependencies (note the required Qt6 binding).

## Credits & license

`concurrency_tools.py` and `napari_in_subprocess.py` were created by
**Nathaniel H. Thayer and Andrew G. York** and come from the AndrewGYork lab
[`tools`](https://github.com/AndrewGYork/tools) repository, which is licensed
under the **GNU General Public License v2.0** (see [`LICENSE`](LICENSE)).

This repository (`tools-patched`) is a vendored, patched copy of just those two
files and is therefore **also distributed under GPL‑2.0**. Original copyright
remains with the authors above; the modifications are documented in
[`PATCHES.md`](PATCHES.md) and in the header of each modified file, as required
by GPL‑2.0 §2(a).

Provenance (pinned upstream commits):

- `napari_in_subprocess.py` — patched; baseline
  [`412171c3`](https://github.com/AndrewGYork/tools/blob/412171c3fa5e5cc8997f36ef3941d7a2f1f40686/napari_in_subprocess.py).
- `concurrency_tools.py` — unmodified upstream snapshot (~2024‑05‑31); see
  [upstream history](https://github.com/AndrewGYork/tools/commits/master/concurrency_tools.py).
