#!/usr/bin/python
# coding=utf-8
#
# Ranger: Explore your forest of files from inside your terminal
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
#
# ----------------------------------------------------------------------------
#
# An embedded shell script. It allows you to change the directory
# of the parent shell to the last visited directory in ranger after exit.
# For more information, check out doc/cd-after-exit.txt
# To enable this, start ranger with:
#     source /path/ranger /path/ranger
"""":
if [ $1 ]; then
	ranger_exec="$1"
	shift
	cd "`exec $ranger_exec --cd-after-exit $@ 3>&1 1>&2 2>&3 3>&-`"
	unset ranger_exec
else
	echo "usage: source path/to/ranger.py path/to/ranger.py"
fi
return 1
"""

# Redefine the docstring, since the previous one was hijacked to
# embed a shellscript.
__doc__ = """Ranger - file browser for the unix terminal"""


# Importing the main method may fail if the ranger directory
# is neither in the same directory as this file, nor in one of
# pythons global import paths.
try:
	from ranger.__main__ import main

except ImportError:
	import sys
	if '-d' not in sys.argv and '--debug' not in sys.argv:
		print("Can't import the main module.")
		print("To run an uninstalled copy of ranger,")
		print("launch ranger.py in the top directory.")
	else:
		raise

else:
	main()

