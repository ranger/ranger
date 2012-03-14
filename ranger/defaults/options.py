# -*- coding: utf-8 -*-
# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
# This configuration file is licensed under the same terms as ranger.
# ===================================================================
# This is the main configuration file of ranger.  It consists of python
# code, but fear not, you don't need any python knowledge for changing
# the settings.
#
# Lines beginning with # are comments.  To enable a line, remove the #.
#
# You can customize ranger in the file ~/.config/ranger/options.py.
# It has the same syntax as this file.  In fact, you can just copy this
# file there with `ranger --copy-config=options' and make your modifications.
# But make sure you update your configs when you update ranger.
# ===================================================================

from ranger.api.options import *

# Load the deault rc.conf file?  If you've copied it to your configuration
# direcory, then you should deactivate this option.
load_default_rc = True

# How many columns are there, and what are their relative widths?
column_ratios = (1, 3, 4)

# Which files should be hidden?  Toggle this by typing `zh' or
# changing the setting `show_hidden'
hidden_filter = regexp(
	r'^\.|\.(?:pyc|pyo|bak|swp)$|^lost\+found$|^__(py)?cache__$')
show_hidden = False

# Which script is used to generate file previews?
# ranger ships with scope.sh, a script that calls external programs (see
# README for dependencies) to preview images, archives, etc.
preview_script = '~/.config/ranger/scope.sh'

# Use that external preview script or display internal plain text previews?
use_preview_script = True

# Use a unicode "..." character to mark cut-off filenames?
unicode_ellipsis = False

# Show dotfiles in the bookmark preview box?
show_hidden_bookmarks = True

# Which colorscheme to use?  These colorschemes are available by default:
# default, default88, jungle, snow
# Snow is monochrome and default88 uses 88 colors.
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

# Enable the mouse support?
mouse_enabled = True

# Display the file size in the main column or status bar?
display_size_in_main_column = True
display_size_in_status_bar = False

# Display files tags in all columns or only in main column?
display_tags_in_all_columns = True

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

# You can display the "real" cumulative size of directories by using the
# command :get_cumulative_size or typing "dc".  The size is expensive to
# calculate and will not be updated automatically.  You can choose
# to update it automatically though by turning on this option:
autoupdate_cumulative_size = False

# Makes sense for screen readers:
show_cursor = False

# One of: size, basename, mtime, type
sort = 'natural'
sort_reverse = False
sort_case_insensitive = True
sort_directories_first = True

# Enable this if key combinations with the Alt Key don't work for you.
# (Especially on xterm)
xterm_alt_key = False

# A function that is called when the user interface is being set up.
init_function = None

# You can use it to initialize some custom functionality or bind singals
#def init_function(fm):
#	fm.notify("Hello :)")
#	def on_tab_change(signal):
#		signal.origin.notify("Changing tab! Yay!")
#	fm.signal_bind("tab.change", on_tab_change)

# The color scheme overlay.  Explained below.
colorscheme_overlay = None

## Apply an overlay function to the colorscheme.  It will be called with
## 4 arguments: the context and the 3 values (fg, bg, attr) returned by
## the original use() function of your colorscheme.  The return value
## must be a 3-tuple of (fg, bg, attr).
## Note: Here, the colors/attributes aren't directly imported into
## the namespace but have to be accessed with color.xyz.

#from ranger.gui import color
#def colorscheme_overlay(context, fg, bg, attr):
#	if context.directory and attr & color.bold and \
#			not any((context.marked, context.selected)):
#		attr ^= color.bold  # I don't like bold directories!
#
#	if context.main_column and context.selected:
#		fg, bg = color.red, color.default  # To highlight the main column!
#
#	return fg, bg, attr


# ===================================================================
# Beware: from here on, you are on your own.  This part requires python
# knowledge.
#
# Since python is a dynamic language, it gives you the power to replace any
# part of ranger without touching the code.  This is commonly referred to as
# Monkey Patching and can be helpful if you, for some reason, don't want to
# modify rangers code directly.  Just remember: the more you mess around, the
# more likely it is to break when you switch to another version.
#
# Here are some practical examples of monkey patching.
#
# Technical information:  This file is imported as a python module.  If a
# variable has the name of a setting, ranger will attempt to use it to change
# that setting.  You can write "del <variable-name>" to avoid that.
# ===================================================================
# Add a new sorting algorithm: Random sort.
# Enable this with :set sort=random

#from ranger.fsobject.directory import Directory
#from random import random
#Directory.sort_dict['random'] = lambda path: random()

# ===================================================================
# A function that changes which files are displayed.  This is more powerful
# than the hidden_filter setting since this function has more information.

## Save the original filter function
#import ranger.fsobject.directory
#old_accept_file = ranger.fsobject.directory.accept_file
#
## Define a new one
#def accept_file_MOD(fname, mypath, hidden_filter, name_filter):
#	if hidden_filter and mypath == '/' and fname in ('boot', 'sbin', 'proc', 'sys'):
#		return False
#	else:
#		return old_accept_file(fname, mypath, hidden_filter, name_filter)
#
## Overwrite the old function
#import ranger.fsobject.directory
#ranger.fsobject.directory.accept_file = accept_file_MOD

# ===================================================================
# A function that adds an additional macro.  Test this with :shell -p echo %date

## Save the original macro function
#import ranger.core.actions
#old_get_macros = ranger.core.actions.Actions._get_macros
#
## Define a new macro function
#import time
#def get_macros_MOD(self):
#	macros = old_get_macros(self)
#	macros['date'] = time.strftime('%m/%d/%Y')
#	return macros
#
## Overwrite the old one
#ranger.core.actions.Actions._get_macros = get_macros_MOD
