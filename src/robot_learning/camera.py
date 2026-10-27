"""Fixed camera settings for recording, and the image measures used to choose them.

A UVC webcam left on auto refocuses and re-exposes as the arm moves, so every episode looks a little
different. Settings go through `uvcc` (npm) and frames through ffmpeg's AVFoundation input, so
grabbing frames is macOS-only. Read-backs can go stale (a C920 once reported gain 255 while its image
showed gain 100), so each value is read back right after it is set, and settings are judged by the
image.
"""

import json
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

Roi = tuple[int, int, int, int]  # x0, y0, x1, y1 in pixels


@dataclass(frozen=True)
class Uvcc:
    """One camera's UVC controls through the `uvcc` command-line tool."""

    vendor: int = 1133  # Logitech
    product: int = 2277  # this desk's HD Pro Webcam C920 (`uvcc devices` lists yours)
    timeout: float = 30.0

    def _run(self, *cmd: str) -> str:
        out = subprocess.run(
            ["uvcc", "--vendor", str(self.vendor), "--product", str(self.product), *cmd],
            check=True, capture_output=True, text=True, timeout=self.timeout,
        )
        return out.stdout.strip()

    def set(self, control: str, value: int) -> None:
        self._run("set", control, str(value))

    def get(self, control: str) -> int:
        return int(self._run("get", control))


@dataclass(frozen=True)
class Grabber:
    """Frames from a camera by its AVFoundation name, at the resolution we record at."""

    camera: str = "HD Pro Webcam C920"
    size: str = "640x480"
    fps: int = 30
    timeout: float = 60.0

    def _ffmpeg(self, *output: str) -> None:
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "avfoundation",
               "-pixel_format", "uyvy422", "-framerate", str(self.fps), "-video_size", self.size,
               "-i", self.camera, *output]
        subprocess.run(cmd, check=True, capture_output=True, timeout=self.timeout)

    def frame(self, path: Path, warmup: int = 15) -> np.ndarray:
        """Save and return (BGR) the last of `warmup` frames, so the camera has settled."""
        self._ffmpeg("-frames:v", str(warmup), "-update", "1", str(path))
        img = cv2.imread(str(path))
        if img is None:
            raise RuntimeError(f"no frame written to {path}")
        return img

    def clip(self, path: Path, seconds: float = 2.0, skip: int = 10) -> list[np.ndarray]:
        """Record a near-lossless clip and return its frames (BGR), dropping the first `skip`."""
        self._ffmpeg("-t", str(seconds), "-c:v", "libx264", "-crf", "8", str(path))
        cap, frames = cv2.VideoCapture(str(path)), []
        while True:
            ok, f = cap.read()
            if not ok:
                break
            frames.append(f)
        cap.release()
        return frames[skip:]


# --- settings -----------------------------------------------------------------------------------


def load_settings(path: Path) -> dict[str, int]:
    """Controls in file order; keys starting with `_` are notes. Order matters: modes before values."""
    return {k: v for k, v in json.loads(Path(path).read_text()).items() if not k.startswith("_")}


def apply_settings(
    settings: Mapping[str, int], set_: Callable[[str, int], None], get: Callable[[str], int]
) -> dict[str, int]:
    """Set each control in order and read it back straight away; returns the read-backs."""
    read_back = {}
    for control, value in settings.items():
        set_(control, value)
        read_back[control] = get(control)
    return read_back


def mismatches(wanted: Mapping[str, int], read_back: Mapping[str, int]) -> list[str]:
    return [c for c, v in wanted.items() if read_back.get(c) != v]


# --- image measures -----------------------------------------------------------------------------


def crop(img: np.ndarray, roi: Roi) -> np.ndarray:
    x0, y0, x1, y1 = roi
    return img[y0:y1, x0:x1]


def gray(img: np.ndarray) -> np.ndarray:
    return img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def sharpness(img: np.ndarray, roi: Roi) -> float:
    """Variance of the Laplacian: more fine edge detail gives a higher value."""
    return float(cv2.Laplacian(gray(crop(img, roi)), cv2.CV_64F).var())


def luma(img: np.ndarray, roi: Roi) -> float:
    return float(gray(crop(img, roi)).mean())


def mean_rgb(img: np.ndarray, roi: Roi) -> tuple[float, float, float]:
    """Mean colour of a BGR image's region, as (R, G, B)."""
    b, g, r = crop(img, roi).reshape(-1, 3).mean(0)
    return float(r), float(g), float(b)


def clipped_fraction(img: np.ndarray, roi: Roi, level: int = 250) -> float:
    """Fraction of pixels with any channel at or above `level`: blown-out highlights."""
    c = crop(img, roi)
    hot = c >= level
    return float((hot.any(-1) if c.ndim == 3 else hot).mean())


def colour_cast(rgb: tuple[float, float, float]) -> float:
    """Zero for a neutral grey; grows with a red-blue or green-magenta tint."""
    r, g, b = rgb
    return abs(r - b) + abs(g - (r + b) / 2)


def flicker_pct(frames: list[np.ndarray], roi: Roi) -> float:
    """Frame-to-frame spread of a region's brightness, as % of its mean (mains flicker shows here)."""
    lumas = np.array([luma(f, roi) for f in frames])
    return float(100 * lumas.std() / lumas.mean())


def temporal_noise(frames: list[np.ndarray], roi: Roi) -> float:
    """Mean over pixels of each pixel's std over frames, in grey levels, for a still scene."""
    stack = np.stack([gray(crop(f, roi)).astype(float) for f in frames])
    return float(stack.std(0).mean())
