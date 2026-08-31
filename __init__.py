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

from anki.utils import pointVersion

from .shige_config.popup_config import set_gui_hook_change_log
set_gui_hook_change_log()

# from anki import version
# assert version.startswith("2.1.")
# minor_ver = int(version.split(".")[-1])

minor_ver = pointVersion()

COMPAT = {
    # find_and_replace
    "find_replace": minor_ver >= 28,
    # media.write_data()
    "write_data": minor_ver >= 22,
    # find_and_replace returns OpChangesWithCount
    "find_replace_cnt": minor_ver >= 45

}

from . import editor
