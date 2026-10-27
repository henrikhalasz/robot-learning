"""Measure brightness, clipping, flicker and noise over a grid of manual exposure x gain.

    uv run scripts/camera_exposure_grid.py --exposures 156 312 --gains 0 32 64 100 128

Exposure is in 100 µs units. Cameras snap exposure to steps of their own, so each value is read back
and the image decides. Needs a still scene: a plain, empty patch of the work surface in --white-roi
and the arm in --arm-roi. Holds white balance fixed at --wb so colour doesn't drift during the grid.
"""

import argparse
import time
from pathlib import Path

import cv2

from robot_learning.camera import (Grabber, Uvcc, clipped_fraction, flicker_pct, luma, temporal_noise)
from robot_learning.runinfo import default_out, run_info, write_json

p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
p.add_argument("--exposures", type=int, nargs="+", default=[156, 200, 312])
p.add_argument("--gains", type=int, nargs="+", default=[0, 32, 64, 100, 128])
p.add_argument("--wb", type=int, default=3000)
p.add_argument("--white-roi", type=int, nargs=4, default=[100, 300, 300, 450])
p.add_argument("--arm-roi", type=int, nargs=4, default=[290, 90, 480, 260])
p.add_argument("--seconds", type=float, default=2.0, help="clip length per setting")
p.add_argument("--vendor", type=int, default=1133)
p.add_argument("--product", type=int, default=2277)
p.add_argument("--camera", default="HD Pro Webcam C920")
p.add_argument("--size", default="640x480")
p.add_argument("--out", type=Path, default=None)
args = p.parse_args()
out = args.out or default_out("camera_exposure_grid")
out.mkdir(parents=True, exist_ok=True)
white, arm = tuple(args.white_roi), tuple(args.arm_roi)
uvcc, grab = Uvcc(args.vendor, args.product), Grabber(args.camera, args.size)


def measure(name: str) -> dict:
    frames = grab.clip(out / f"{name}.mp4", args.seconds)
    cv2.imwrite(str(out / f"{name}.jpg"), frames[-1])
    return {"desk_luma": round(luma(frames[-1], white), 1), "arm_luma": round(luma(frames[-1], arm), 1),
            "desk_clipped": round(clipped_fraction(frames[-1], white), 3),
            "flicker_pct": round(flicker_pct(frames, white), 3),
            "noise_desk": round(temporal_noise(frames, white), 2), "noise_arm": round(temporal_noise(frames, arm), 2)}


# What the camera does on its own, for comparison.
uvcc.set("auto_exposure_mode", 8)
uvcc.set("auto_white_balance_temperature", 1)
time.sleep(3)
auto = {**measure("auto"), "exposure_read": uvcc.get("absolute_exposure_time"), "gain_read": uvcc.get("gain")}
print("auto", auto, flush=True)

uvcc.set("auto_exposure_mode", 1)
uvcc.set("auto_white_balance_temperature", 0)
uvcc.set("white_balance_temperature", args.wb)
rows = []
for e in args.exposures:
    for g in args.gains:
        uvcc.set("absolute_exposure_time", e)
        uvcc.set("gain", g)
        row = {"exposure_set": e, "exposure_read": uvcc.get("absolute_exposure_time"), "gain": g,
               **measure(f"e{e}_g{g}")}
        rows.append(row)
        print(row, flush=True)

write_json(out / "grid.json", {**run_info({k: str(v) for k, v in vars(args).items()}), "auto": auto, "grid": rows})
print(f"results in {out}/grid.json; camera left at the last grid setting (re-run camera_apply.py)")
