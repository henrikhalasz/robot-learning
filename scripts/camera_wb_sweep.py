"""Choose a fixed white balance: the temperature at which a plain white surface comes out most neutral.

    uv run scripts/camera_wb_sweep.py --white-roi 100 300 300 450

Run it after the exposure is fixed (camera_apply.py), with --white-roi on an empty patch of a white
work surface that is not blown out. Leaves the camera at the most neutral temperature.
"""

import argparse
from pathlib import Path

from robot_learning.camera import Grabber, Uvcc, clipped_fraction, colour_cast, mean_rgb
from robot_learning.runinfo import default_out, run_info, write_json

p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
p.add_argument("--temps", type=int, nargs="+", default=list(range(2000, 6501, 250)))
p.add_argument("--white-roi", type=int, nargs=4, default=[100, 300, 300, 450])
p.add_argument("--vendor", type=int, default=1133)
p.add_argument("--product", type=int, default=2277)
p.add_argument("--camera", default="HD Pro Webcam C920")
p.add_argument("--size", default="640x480")
p.add_argument("--out", type=Path, default=None)
args = p.parse_args()
out = args.out or default_out("camera_wb_sweep")
out.mkdir(parents=True, exist_ok=True)
white = tuple(args.white_roi)
uvcc, grab = Uvcc(args.vendor, args.product), Grabber(args.camera, args.size)

uvcc.set("auto_white_balance_temperature", 0)
sweep = {}
for t in args.temps:
    uvcc.set("white_balance_temperature", t)
    img = grab.frame(out / f"wb_{t}.jpg")
    rgb = mean_rgb(img, white)
    sweep[t] = {"desk_rgb": [round(c, 1) for c in rgb], "cast": round(colour_cast(rgb), 1),
                "desk_clipped": round(clipped_fraction(img, white), 3)}
    print(f"{t:4d} K  desk rgb {sweep[t]['desk_rgb']}  cast {sweep[t]['cast']:5.1f}  "
          f"clipped {sweep[t]['desk_clipped']}", flush=True)

best = min(sweep, key=lambda t: sweep[t]["cast"])
uvcc.set("white_balance_temperature", best)
write_json(out / "wb.json", {**run_info({k: str(v) for k, v in vars(args).items()}),
                             "exposure_read": uvcc.get("absolute_exposure_time"), "gain_read": uvcc.get("gain"),
                             "sweep": sweep, "best": best})
print(f"most neutral at {best} K; camera left there; results in {out}/wb.json")
