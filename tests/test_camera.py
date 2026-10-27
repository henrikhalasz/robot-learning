import json

import cv2
import numpy as np
import pytest

from robot_learning.camera import (apply_settings, clipped_fraction, colour_cast, flicker_pct, load_settings,
                                   luma, mean_rgb, mismatches, sharpness, temporal_noise)

FULL = (0, 0, 64, 64)


def texture(seed=0):
    return np.random.default_rng(seed).integers(0, 256, (64, 64, 3), dtype=np.uint8)


def test_sharpness_drops_when_blurred():
    img = texture()
    assert sharpness(img, FULL) > 5 * sharpness(cv2.GaussianBlur(img, (9, 9), 3), FULL)


def test_mean_rgb_reads_bgr_as_rgb():
    img = np.zeros((4, 4, 3), np.uint8)
    img[..., 2] = 200  # red in BGR
    assert mean_rgb(img, (0, 0, 4, 4)) == (200.0, 0.0, 0.0)


def test_colour_cast_is_zero_for_grey_and_positive_for_a_tint():
    assert colour_cast((128, 128, 128)) == 0
    assert colour_cast((150, 128, 110)) > 0
    assert colour_cast((128, 150, 128)) > 0


def test_clipped_fraction_counts_any_saturated_channel():
    img = np.full((10, 10, 3), 100, np.uint8)
    img[:5, :, 0] = 255
    assert clipped_fraction(img, (0, 0, 10, 10)) == pytest.approx(0.5)


def test_flicker_is_zero_for_steady_frames_and_seen_for_alternating_ones():
    steady = [np.full((8, 8, 3), 120, np.uint8)] * 6
    pulsing = [np.full((8, 8, 3), v, np.uint8) for v in (110, 130) * 3]
    assert flicker_pct(steady, (0, 0, 8, 8)) == 0
    assert flicker_pct(pulsing, (0, 0, 8, 8)) == pytest.approx(100 * 10 / 120, rel=0.02)


def test_temporal_noise_is_zero_for_a_still_scene():
    still = [texture()] * 5
    noisy = [np.clip(texture().astype(int) + np.random.default_rng(i).normal(0, 3, (64, 64, 3)), 0, 255)
             .astype(np.uint8) for i in range(5)]
    assert temporal_noise(still, FULL) == 0
    assert temporal_noise(noisy, FULL) > 1


def test_luma_of_grey():
    assert luma(np.full((4, 4, 3), 77, np.uint8), (0, 0, 4, 4)) == pytest.approx(77, abs=1)


def test_load_settings_skips_notes_and_keeps_order(tmp_path):
    path = tmp_path / "s.json"
    path.write_text(json.dumps({"_why": "note", "auto_focus": 0, "absolute_focus": 20}))
    assert list(load_settings(path).items()) == [("auto_focus", 0), ("absolute_focus", 20)]


def test_apply_settings_sets_in_order_reads_back_each_and_flags_mismatches():
    calls, camera = [], {}

    def set_(c, v):
        calls.append(("set", c))
        camera[c] = 156 if c == "absolute_exposure_time" else v  # a camera that snaps exposure

    def get(c):
        calls.append(("get", c))
        return camera[c]

    wanted = {"auto_exposure_mode": 1, "absolute_exposure_time": 200}
    read_back = apply_settings(wanted, set_, get)
    assert calls == [("set", "auto_exposure_mode"), ("get", "auto_exposure_mode"),
                     ("set", "absolute_exposure_time"), ("get", "absolute_exposure_time")]
    assert mismatches(wanted, read_back) == ["absolute_exposure_time"]

