import json

from robot_learning.runinfo import REPO, default_out, run_info, write_json


def test_run_info_records_args_and_commit():
    info = run_info({"seed": 0})
    assert info["args"] == {"seed": 0}
    assert len(info["git_commit"]) == 40
    assert isinstance(info["git_dirty"], bool)


def test_default_out_is_under_ignored_outputs():
    assert default_out("demo").relative_to(REPO).parts[:2] == ("outputs", "demo")


def test_write_json_creates_parents(tmp_path):
    path = tmp_path / "a" / "b.json"
    write_json(path, {"x": 1})
    assert json.loads(path.read_text()) == {"x": 1}


def test_run_info_stores_repo_paths_relative():
    info = run_info({"settings": str(REPO / "rig" / "c920.json"), "elsewhere": "/tmp/x"})
    assert info["args"] == {"settings": "rig/c920.json", "elsewhere": "/tmp/x"}
