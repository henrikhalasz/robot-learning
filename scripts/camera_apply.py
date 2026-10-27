"""Apply a camera's fixed settings before recording, check them, and save a reference frame.

    uv run scripts/camera_apply.py                       # rig/c920.json onto the C920
    uv run scripts/camera_apply.py --out outputs/today   # choose where the check goes

Exits non-zero if any control reads back different from the file.
"""

import argparse
import sys
from pathlib import Path

from robot_learning.camera import Grabber, Uvcc, apply_settings, load_settings, mismatches
from robot_learning.runinfo import REPO, default_out, run_info, write_json

p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
p.add_argument("--settings", type=Path, default=REPO / "rig" / "c920.json")
p.add_argument("--vendor", type=int, default=1133)
p.add_argument("--product", type=int, default=2277)
p.add_argument("--camera", default="HD Pro Webcam C920", help="AVFoundation device name")
p.add_argument("--size", default="640x480")
p.add_argument("--out", type=Path, default=None)
args = p.parse_args()
out = args.out or default_out("camera_apply")
out.mkdir(parents=True, exist_ok=True)

uvcc = Uvcc(args.vendor, args.product)
wanted = load_settings(args.settings)
read_back = apply_settings(wanted, uvcc.set, uvcc.get)
for control, value in wanted.items():
    flag = "" if read_back[control] == value else "   <-- MISMATCH"
    print(f"{control:32s} set {value:5d}  read {read_back[control]:5d}{flag}")

Grabber(args.camera, args.size).frame(out / "reference.jpg")
bad = mismatches(wanted, read_back)
write_json(out / "camera_settings.json",
           {**run_info({k: str(v) for k, v in vars(args).items()}), "wanted": wanted, "read_back": read_back,
            "mismatches": bad})
print(f"saved {out}/reference.jpg and camera_settings.json; mismatches: {bad or 'none'}")
sys.exit(1 if bad else 0)
