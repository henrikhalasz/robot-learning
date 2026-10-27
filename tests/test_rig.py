from robot_learning.camera import load_settings
from robot_learning.runinfo import REPO


def test_rig_c920_settings_put_each_auto_switch_before_its_value():
    keys = list(load_settings(REPO / "rig" / "c920.json"))
    for auto, value in [("auto_exposure_mode", "absolute_exposure_time"), ("auto_exposure_mode", "gain"),
                        ("auto_white_balance_temperature", "white_balance_temperature"),
                        ("auto_focus", "absolute_focus")]:
        assert keys.index(auto) < keys.index(value)
