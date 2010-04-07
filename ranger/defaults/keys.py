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
This is the default key configuration file of ranger.
Syntax for binding keys: map(*keys, fnc)

keys are one or more key-combinations which are either:
* a string
* an integer which represents an ascii code
* a tuple of integers

fnc is a function which is called with the CommandArgument object.

The CommandArgument object has these attributes:
arg.fm: the file manager instance
arg.wdg: the widget or ui instance
arg.n: the number typed before the key combination (if allowed)
arg.keys: the string representation of the used key combination
arg.keybuffer: the keybuffer instance

Check ranger.keyapi for more information
"""

# NOTE: The "map" object used below is a callable CommandList
# object and NOT the builtin python map function!

from ranger.api.keys import *


# ---------------------------------------------------------
# Define keys for everywhere:
map = keymanager['general']
@map('<dir>')
def move(arg):
	arg.wdg.move(narg=arg.n, **arg.direction)

map('Q', fm.exit())
map('<C-L>', fm.redraw_window())

# ---------------------------------------------------------
# Define keys in "general" context:
map = keymanager['general']


map('j', fm.move(down=1))
map('Q', fm.exit())

# --------------------------------------------------------- history
map('H', fm.history_go(-1))
map('L', fm.history_go(1))

# ----------------------------------------------- tagging / marking
map('t', fm.tag_toggle())
map('T', fm.tag_remove())

map(' ', fm.mark(toggle=True))
map('v', fm.mark(all=True, toggle=True))
map('V', fm.mark(all=True, val=False))

# ---------------------------------------------------------
# Define direction keys
map = keymanager.get_context('directions')
map('<down>', dir=Direction(down=1))
map('<up>', dir=Direction(down=-1))
map('<left>', dir=Direction(right=-1))
map('<right>', dir=Direction(right=1))
map('<home>', dir=Direction(down=0, absolute=True))
map('<end>', dir=Direction(down=-1, absolute=True))
map('<pagedown>', dir=Direction(down=1, pages=True))
map('<pageup>', dir=Direction(down=-1, pages=True))
map('%<any>', dir=Direction(down=1, percentage=True, absolute=True))
map('<space>', dir=Direction(down=1, pages=True))
map('<CR>', dir=Direction(down=1))
