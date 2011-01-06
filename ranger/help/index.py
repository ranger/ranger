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
                    ranger %s - main help file
                                                                     k
    Move around:  Use the cursor keys, or "h" to go left,          h   l
                  "j" to go down, "k" to go up, "l" to go right.     j
   Close Ranger:  Type "Q"
  Specific help:  Type "?", prepended with a number:

	|0?|	This index
	|1?|	Basic movement and browsing
	|2?|	Running Files
	|3?|	The console
	|4?|	File operations
	|5?|	Ranger invocation


==============================================================================
0.1. About ranger

Ranger is a free console file manager that gives you greater flexibility
and a good overview of your files without having to leave your *nix console.
It visualizes the directory tree in two dimensions: the directory hierarchy
on one, lists of files on the other, with a preview to the right so you know
where you'll be going.

The default keys are similar to those of Vim, Emacs and Midnight Commander,
though Ranger is easily controllable with just the arrow keys or the mouse.

The program is written in Python (2.6 or 3.1) and uses curses for the
text-based user interface.


==============================================================================
0.2. About these help pages

Annotations like |1?| indicate that the topic is explained in more
detail in chapter 1. You can type 1? to view it.
You can type 16? to open chapter 1, paragraph 6.


==============================================================================
0.3. Copying

Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


==============================================================================
"""

import ranger
__doc__ %= ranger.__version__
# vim:tw=78:sw=4:sts=8:ts=8:ft=help
