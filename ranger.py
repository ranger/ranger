#!/usr/bin/python
# coding=utf-8
# ranger: Explore your forest of files from inside your terminal
#
# Copyright (c) 2009, 2010 hut <hut@lavabit.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
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
	cd `exec $ranger_exec --cd-after-exit $@ 3>&1 1>&2 2>&3 3>&-`
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
	from ranger import main

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

