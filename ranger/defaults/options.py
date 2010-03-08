# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This is the default configuration file of ranger.
If you do any changes, make sure the import-line stays
intact and the type of the value stays the same.
"""

from ranger.api.options import *

one_kb = 1024

colorscheme = colorschemes.default

max_history_size = 20
max_filesize_for_preview = 300 * one_kb
scroll_offset = 2
preview_files = True
flushinput = True

sort = 'basename'
reverse = False
directories_first = True

show_hidden = False
collapse_preview = True
autosave_bookmarks = True
update_title = False

show_cursor = False

hidden_filter = regexp(r'^\.|~$|\.(:?pyc|pyo|bak|swp)$')
