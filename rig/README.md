# Rig

The desk: two SO-101 followers, one leader, an Innomaker U20CAM wrist camera on each follower and a
Logitech C920 scene camera, on a MacBook Pro whose three USB-C ports each have their own USB
controller, with a USB-C monitor.

## Wiring

**USB.** Every device here is USB 2. A webcam reserves a large fixed share of its USB 2 link before
it streams, so two cameras on one link may fail to open or drop frames; the arms use almost nothing
and can share. So each camera gets its own link, and a monitor's built-in hub counts as one link
however many ports it has.

```
Mac
├─ port 1 ── monitor (picture, charging, and its hub: one USB 2 link)
│              ├─ USB-A ── scene camera (C920)
│              └─ USB-A ── 4-port hub ── follower 1, follower 2, leader (each arm's driver board)
├─ port 2 ── USB-C→A adapter ── 2 m extension ── wrist camera on follower 1
└─ port 3 ── USB-C→A adapter ── 2 m extension ── wrist camera on follower 2
```

An arm's serial port, `/dev/tty.usbmodem…`, carries its driver board's USB serial number (seen on
the first follower's board), so the name follows the board, not the hub port.

**Power.** Each arm has its own brick, plugged into its driver board; USB carries only data. Match
the brick to the servos: the leader's servos are always the 7.4 V type and take 5 V; a follower
takes 5 V for 7.4 V servos and 12 V for 12 V servos. A 12 V brick on 7.4 V servos can damage them,
so label each brick with its arm. The servos' `Present_Voltage` register reads the supply.

## Scene camera placement

- Frame the task, not the room: the work area and the gripper's whole path, with a margin.
- Put the camera in front of or beside the arm, never behind it, looking down at an angle so the
  gripper's height above the work surface shows.
- Mount it rigidly and never move it; tape marks on the mount show if it shifts.
- Keep the leader, the operator and anything else that moves out of frame. The leader's pose is the
  action being recorded, so a policy that can see it learns to read the action off the leader.
- Frame it at the recording resolution: at 640×480 the C920 keeps only the centre 4:3 of its 16:9
  view.
- Light the work area evenly (a lamp bounced off a wall, the lamp itself out of frame) and keep the
  light the same for every episode.

## Scene camera settings

On auto the camera refocuses and re-exposes as the arm moves through the frame, so episodes differ
for reasons unrelated to the task. [`c920.json`](c920.json) fixes everything; apply it before every
session (the camera may forget its settings when unplugged; not yet verified):

```bash
uv run scripts/camera_apply.py      # sets each control in order, reads it back, saves a reference frame
```

How the values were chosen. Each file in [`c920-tuning/`](c920-tuning/) records the arguments and
commit that produced it.

- **Focus** ([`focus-sweep.json`](c920-tuning/focus-sweep.json)): sharpness of the region holding the
  arm over every focus value. It has a flat sharp plateau at the low end and drops steeply after it;
  the chosen value sits inside the plateau, clear of the drop.
- **Exposure and gain** ([`exposure-grid.json`](c920-tuning/exposure-grid.json)): brightness, clipping,
  flicker and noise for each pair, plus what auto exposure does. Two pairs reach about the same
  brightness without clipping; the chosen one has the shorter exposure, which halves motion blur
  for a small difference in noise. Flicker is negligible under this lighting.
- **White balance** ([`white-balance.json`](c920-tuning/white-balance.json)): the colour cast of an
  empty patch of the white desk at each temperature; the chosen temperature is the most neutral.
- **Check** ([`apply-check.json`](c920-tuning/apply-check.json)): every control read back as set.

C920 behaviour to know:

- Manual exposure snaps to the camera's own steps: a value between two steps gives the lower step's
  image (in `exposure-grid.json`, `exposure_set` 200 reads back and images as 156).
- Read-backs can go stale: after a long sweep the camera once reported a gain different from the
  one its image showed. That is why settings live in `c920.json`, are read back right after each
  set, and are judged by the image, rather than saved with `uvcc export`.
- The mains-flicker filter shipped set for 60 Hz; UK mains is 50 Hz (`power_line_frequency: 1`).

Re-tune when the lighting, the camera or its framing changes. Regions are pixel boxes
`X0 Y0 X1 Y1` in the 640×480 frame: `--roi` and `--arm-roi` on the arm, `--white-roi` on an empty
patch of the work surface.

```bash
uv run scripts/camera_focus_sweep.py --roi 260 40 580 280
uv run scripts/camera_exposure_grid.py --white-roi 100 300 300 450 --arm-roi 290 90 480 260
# put the chosen focus, exposure and gain into c920.json, then
uv run scripts/camera_apply.py
uv run scripts/camera_wb_sweep.py --white-roi 100 300 300 450
# put the chosen temperature into c920.json, then apply again
```

## Tools

- macOS: frames come through AVFoundation.
- ffmpeg: `brew install ffmpeg`.
- [uvcc](https://github.com/joelpurra/uvcc): `npm install --global uvcc`. `uvcc devices` lists each
  camera's vendor and product IDs; the scripts default to this desk's C920.
