"""What every run saves next to its output: arguments, git commit, time and machine."""

import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()


def _portable(value):
    """Paths inside the repo are stored relative to it, so outputs don't carry this machine's layout."""
    s = str(value)
    return s[len(str(REPO)) + 1:] if s.startswith(f"{REPO}/") else value


def run_info(args: dict) -> dict:
    """The record that makes an output reproducible: pass `vars(argparse_namespace)`."""
    return {
        "args": {k: _portable(v) for k, v in args.items()},
        "git_commit": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain")),
        "time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "machine": f"{platform.system()} {platform.release()} {platform.machine()}",
    }


def default_out(script: str) -> Path:
    """`outputs/<script>/<timestamp>/`, which git ignores."""
    return REPO / "outputs" / script / datetime.now().strftime("%Y%m%d-%H%M%S")


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1) + "\n")
