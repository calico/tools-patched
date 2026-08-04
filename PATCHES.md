# PATCHES

This repository (`tools-patched`) is a **vendored, patched copy** of two modules
from Andrew G. York's [`tools`](https://github.com/AndrewGYork/tools) repository:

- `concurrency_tools.py`
- `napari_in_subprocess.py`

Original authors: **Nathaniel H. Thayer and Andrew G. York**.
Upstream license: **GPL‑2.0** — this repo inherits it (see [`LICENSE`](LICENSE)).

This file records what was changed relative to upstream, so the modifications are
transparent and re-applyable when upstream updates, as required by GPL‑2.0 §2(a).

---

## `napari_in_subprocess.py` — PATCHED

**Upstream baseline:** commit
[`412171c3`](https://github.com/AndrewGYork/tools/blob/412171c3fa5e5cc8997f36ef3941d7a2f1f40686/napari_in_subprocess.py)

**2026-08-03 — amsikking: fix canvas corruption on recent NVIDIA drivers**

Symptom: after a Windows/NVIDIA driver update (observed on 595.95), the napari
GPU canvas rendered as a corrupt **triangle** (napari 0.4.19) or **black**
(napari 0.8.0). Root cause was the **Qt5 binding** (PyQt5/PySide2), not napari,
vispy, or the image data.

Changes:

1. **Force a Qt6 binding in the child process.** Added `_select_qt_binding()`,
   which sets `QT_API` to `PySide6` (preferred) or `PyQt6` *before* qtpy/napari
   are imported. Runs **only inside the napari child process**, so the parent
   application's Qt binding is never touched.
2. **Replace `napari.gui_qt()` with `napari.run()`.** `gui_qt()` was removed in
   napari 0.5; driving the event loop via `napari.run()` (plus an explicit
   `QApplication` through `_ensure_qapp()`) works on napari 0.4.19 through 0.8+.
3. **Defer `napari` / `qtpy` imports.** Moved these out of module-import time and
   into the child process (`_napari_child_loop` / `_NapariDisplay.__init__`), so
   importing this module in the parent loads neither napari nor qtpy and cannot
   disturb the surrounding app's Qt configuration.

Public API (`display`, `_NapariDisplay`, `show_image`, `close`) is unchanged.

To review the exact diff against the baseline:

```bash
curl -fsSL https://raw.githubusercontent.com/AndrewGYork/tools/412171c3fa5e5cc8997f36ef3941d7a2f1f40686/napari_in_subprocess.py -o upstream_napari.py
diff upstream_napari.py napari_in_subprocess.py
```

---

## `concurrency_tools.py` — UNMODIFIED

Pristine upstream snapshot, dated **~2024‑05‑31**. No functional changes have
been made; only a provenance/attribution header comment was added at the top.

Upstream has since drifted (e.g. an added `test_custody_release` test and a
`resource` → `self.target_resource` refactor). This copy is intentionally pinned
to the older snapshot the downstream projects were validated against. When you
update it, replace the file with the new upstream copy, re-add the header, and
record the new baseline commit here.
