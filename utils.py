# Copyright (C) BlueGreenMagick 2020-2022 <https://github.com/BlueGreenMagick>
# Copyright (C) Shigeyuki 2025 <http://patreon.com/Shigeyuki>
# License: GNU AGPL version 3 or later <http://www.gnu.org/licenses/agpl.html>

from aqt.qt import Qt
from aqt import mw


def get_addon_id() -> str:
    addon_id = mw.addonManager.addonFromModule(__name__)
    return addon_id or "789309990"


def get_addon_config() -> dict:
    addon_id = get_addon_id()
    config = mw.addonManager.getConfig(addon_id)
    if not isinstance(config, dict):
        config = {}
    return config


def write_addon_config(config: dict):
    addon_id = get_addon_id()
    mw.addonManager.writeConfig(addon_id, config)


def get_config(key: str, hidden: bool = False, notexist: any = None) -> any:
    cfg = get_addon_config()
    if key in cfg:
        return cfg[key]
    if "_hidden" in cfg and isinstance(cfg["_hidden"], dict) and key in cfg["_hidden"]:
        return cfg["_hidden"][key]
    
    # Check camelCase fallback (e.g. replaceAll vs replace_all)
    parts = key.split("_")
    camel = parts[0] + "".join(p.capitalize() for p in parts[1:])
    if camel in cfg:
        return cfg[camel]
    if "_hidden" in cfg and isinstance(cfg["_hidden"], dict) and camel in cfg["_hidden"]:
        return cfg["_hidden"][camel]
        
    return notexist


def set_config(key: str, val: any, hidden: bool = False):
    cfg = get_addon_config()
    cfg[key] = val
    if "_hidden" in cfg and isinstance(cfg["_hidden"], dict):
        cfg["_hidden"][key] = val
    write_addon_config(cfg)


def checked(ch: bool) -> Qt.CheckState:
    if ch:
        return Qt.CheckState.Checked
    else:
        return Qt.CheckState.Unchecked
