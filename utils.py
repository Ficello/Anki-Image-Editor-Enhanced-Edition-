# Copyright (C) BlueGreenMagick 2020-2022 <https://github.com/BlueGreenMagick>
# Copyright (C) Shigeyuki 2025 <http://patreon.com/Shigeyuki>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from aqt.qt import Qt
from aqt import mw

addon = mw.addonManager


def get_config(key, hidden=False, notexist=""):
    config = addon.getConfig(__name__)
    if hidden:
        return config["_hidden"].get(key, notexist)
    else:
        return config[key]

def set_config(key, val, hidden=False):
    config = addon.getConfig(__name__)
    if hidden:
        config["_hidden"][key] = val
    else:
        config[key] = val
    addon.writeConfig(__name__, config)

def checked(ch: bool) -> Qt.CheckState:
    if ch:
        return Qt.CheckState.Checked
    else:
        return Qt.CheckState.Unchecked