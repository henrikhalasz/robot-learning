"""Find a sharp fixed focus: step absolute_focus with autofocus off and score sharpness in a region.

    uv run scripts/camera_focus_sweep.py --roi 260 40 580 280

The region should hold what must be sharp (the arm and the work area). Leaves the camera at the
sharpest focus; copy it into rig/c920.json if it should change.
"""

import argparse
import time
from pathlib import Path

from robot_learning.camera import Grabber, Uvcc, sharpness
from robot_learning.runinfo import default_out, run_info, write_json

p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
p.add_argument("--roi", type=int, nargs=4, metavar=("X0", "Y0", "X1", "Y1"), default=[260, 40, 580, 280])
p.add_argument("--start", type=int, default=0)
p.add_argument("--stop", type=int, default=250)
p.add_argument("--step", type=int, default=10)
p.add_argument("--settle", type=float, default=0.5, help="seconds for the lens to move before grabbing")
p.add_argument("--vendor", type=int, default=1133)
p.add_argument("--product", type=int, default=2277)
p.add_argument("--camera", default="HD Pro Webcam C920")
p.add_argument("--size", default="640x480")
p.add_argument("--out", type=Path, default=None)
args = p.parse_args()
out = args.out or default_out("camera_focus_sweep")
out.mkdir(parents=True, exist_ok=True)

uvcc, grab = Uvcc(args.vendor, args.product), Grabber(args.camera, args.size)
uvcc.set("auto_focus", 0)
scores = {}
for focus in range(args.start, args.stop + 1, args.step):
    uvcc.set("absolute_focus", focus)
    time.sleep(args.settle)
    scores[focus] = sharpness(grab.frame(out / f"focus_{focus:03d}.jpg"), tuple(args.roi))
    print(f"focus {focus:3d}  sharpness {scores[focus]:8.1f}", flush=True)

best = max(scores, key=scores.get)
uvcc.set("absolute_focus", best)
write_json(out / "sweep.json", {**run_info({k: str(v) for k, v in vars(args).items()}),
                                "sharpness_by_focus": scores, "best": best})
print(f"sharpest at focus {best}; camera left there with autofocus off; results in {out}/sweep.json")
