#!/usr/bin/python
# coding=utf-8
# ranger: Browse your files inside the terminal.
# -----------------------------------------------------------------------------

# An embedded shell script. It allows you to change the directory
# of the parent shell to the last visited directory in ranger after exit.
# For more information, check out doc/cd-after-exit.txt
# To enable this, start ranger with:
#     source /path/ranger /path/ranger
"""":
if [ $1 ]; then
	RANGER="$1"
	shift
	cd "`$RANGER --cd-after-exit \"$@\" 3>&1 1>&2 2>&3 3>&-`"
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

except ImportError as errormessage:
	if str(errormessage).endswith("main"):
		print("Can't import the main module.")
		print("To run an uninstalled copy of ranger,")
		print("launch ranger.py in the top directory.")
	else:
		raise

else:
	main()

