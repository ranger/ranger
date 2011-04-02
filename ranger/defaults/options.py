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
method is creating a file at ~/.config/ranger/options.py and adding
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

# Which files should be hidden?  Toggle this by typing `zh' or
# changing the setting `show_hidden'
hidden_filter = regexp(
	r'^\.|\.(?:pyc|pyo|bak|swp)$|^lost\+found$|^__cache__$')
show_hidden = False

# Which script is used to generate file previews?
# Ranger ships with scope.sh, a script that calls external programs (see
# README for dependencies) to preview images, archives, etc.
preview_script = '~/.config/ranger/scope.sh'

# Use that external preview script or display internal plain text previews?
use_preview_script = True

# Use a unicode "..." character to mark cut-off filenames?
unicode_ellipsis = True

# Show dotfiles in the bookmark preview box?
show_hidden_bookmarks = True

# Which colorscheme to use?  These colorschemes are available by default:
# default, default88, texas, jungle, snow
# Snow is monochrome, texas and default88 use 88 colors.
colorscheme = 'default'

# Preview files on the rightmost column?
# And collapse (shrink) the last column if there is nothing to preview?
preview_files = True
preview_directories = True
collapse_preview = True

# Save the console history on exit?
save_console_history = True

# Draw borders around columns?
draw_borders = False
draw_bookmark_borders = True

# Display the directory name in tabs?
dirname_in_tabs = False

# How many columns are there, and what are their relative widths?
column_ratios = (1, 1, 4, 3)

# Enable the mouse support?
mouse_enabled = True

# Display the file size in the main column or status bar?
display_size_in_main_column = True
display_size_in_status_bar = False

# Set a title for the window?
update_title = True

# Shorten the title if it gets long?  The number defines how many
# directories are displayed at once, False turns off this feature.
shorten_title = 3

# Abbreviate $HOME with ~ in the titlebar (first line) of ranger?
tilde_in_titlebar = True

# How many directory-changes or console-commands should be kept in history?
max_history_size = 20
max_console_history_size = 50

# Try to keep so much space between the top/bottom border when scrolling:
scroll_offset = 8

# Flush the input after each key hit?  (Noticable when ranger lags)
flushinput = True

# Padding on the right when there's no preview?
# This allows you to click into the space to run the file.
padding_right = True

# Save bookmarks (used with mX and `X) instantly?
# This helps to synchronize bookmarks between multiple ranger
# instances but leads to *slight* performance loss.
# When false, bookmarks are saved when ranger is exited.
autosave_bookmarks = True

# Makes sense for screen readers:
show_cursor = False

# One of: size, basename, mtime, type
sort = 'basename'
sort_reverse = False
sort_case_insensitive = False
sort_directories_first = True

# Enable this if key combinations with the Alt Key don't work for you.
# (Especially on xterm)
xterm_alt_key = False


# Apply an overlay function to the colorscheme.  It will be called with
# 4 arguments: the context and the 3 values (fg, bg, attr) returned by
# the original use() function of your colorscheme.  The return value
# must be a 3-tuple of (fg, bg, attr).
# Note: Here, the colors/attributes aren't directly imported into
# the namespace but have to be accessed with color.xyz.
def colorscheme_overlay(context, fg, bg, attr):
	if context.directory and attr & color.bold and \
			not any((context.marked, context.selected)):
		attr ^= color.bold  # I don't like bold directories!

	if context.main_column and context.selected:
		fg, bg = color.red, color.default  # To highlight the main column!

	return fg, bg, attr

# The above function was just an example, let's set it back to None
colorscheme_overlay = None
