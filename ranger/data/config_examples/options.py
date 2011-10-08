# ===================================================================
# This is the main configuration file of ranger.  It consists of python
# code, but fear not, you don't need any python knowledge for changing
# the settings.
#
# Lines beginning with # are comments.  To enable a line, remove the #.
#
# Here are the most important settings.  Refer to the man page for
# a list and descriptions of all settings.
# ===================================================================

# This line imports some basic variables
from ranger.api.options import *

# ranger can use a customizable external script for previews.  The included
# default script prints previews of archives, html/pdf documents and even
# images.  This is, however, disabled by default for performance reasons.  Turn
# it on by uncommenting this line:
#use_preview_script = True

# This changes the location of the preview script
#preview_script = "~/.config/ranger/scope.sh"

# Use a simple character-wise sort algorithm instead of the default natural
# sorting.  This is faster, although the difference is hardly noticeable.
#sort = "basename"

# Use a unicode "..." symbol when filenames are truncated.  This is disabled
# by default since some systems don't support unicode+curses well.
#unicode_ellipsis = True

# Uncomment these lines to disable previews by default?
#preview_files = False
#preview_directories = False

# xterm handles the ALT key differently.  If you use xterm, uncomment this line
#xterm_alt_key = True

# Change what files ranger should hide with this setting.  Its value is a
# "regular expression".  If you don't know about them, there are lots of good
# tutorials on the web!  Below is the default value.
#hidden_filter = regexp(r"^\.|\.(?:pyc|pyo|bak|swp)$|^lost\+found$|^__cache__$")


# ===================================================================
# Beware: from here on, you are on your own.  This part requires python
# knowledge.
#
# Since python is a dynamic language, it gives you the power to replace any
# part of ranger without touching the code.  This is commonly referred to as
# Monkey Patching and can be helpful if you, for some reason, don't want to
# modify rangers code directly.  Just remember: the more you mess around, the
# more likely it is to break when you switch to another version.  Here are some
# practical examples of monkey patching.
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

## Define a new one
#def accept_file_MOD(fname, mypath, hidden_filter, name_filter):
#	if mypath == '/' and fname in ('boot', 'sbin', 'proc', 'sys'):
#		return False
#	else:
#		return old_accept_file(fname, mypath, hidden_filter, name_filter)

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

# ===================================================================
