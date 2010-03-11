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

There are two ways of customizing ranger.  The first and recommended
method is creating a file at ~/.ranger/options.py and adding
those lines you want to change.  It might look like this:

from ranger.api.options import *
preview_files = False  # I hate previews!
max_history_size = 2000  # I can afford it.

The other way is directly editing this file.  This will make upgrades
of ranger more complicated though.

Whatever you do, make sure the import-line stays intact and the type
of the values stay the same.
"""

from ranger.api.options import *

# Which files are hidden if show_hidden is False?
hidden_filter = regexp(
	r'lost\+found|^\.|~$|\.(:?pyc|pyo|bak|swp)$')
show_hidden = False

# Which colorscheme to use?  These colorschemes are available by default:
# default, default88, texas, jungle, snow
# Snow is monochrome, texas and default88 use 88 colors.
colorscheme = colorschemes.ice

# Preview files on the rightmost column?
# And collapse the last column if there is nothing to preview?
preview_files = True
max_filesize_for_preview = 300 * 1024  # 300kb
collapse_preview = True

# Specify a title for the window? Some terminals don't support this,
# so it's turned off by default.
update_title = False

# How many directory-changes or console-commands should be kept in history?
max_history_size = 20

# Try to keep so much space between the top/bottom border when scrolling:
scroll_offset = 2

# Flush the input after each key hit?  (Noticable when ranger lags)
flushinput = True

# Save bookmarks (used with mX and `X) instantly?
# This helps to synchronize bookmarks between multiple ranger
# instances but leads to *slight* performance loss.
# When false, bookmarks are saved when ranger is exited.
autosave_bookmarks = True

# Makes sense for screen readers:
show_cursor = False

# One of: size, basename, mtime, type
sort = 'basename'
reverse = False
directories_first = True

