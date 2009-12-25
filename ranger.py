#!/usr/bin/python -OO
# coding=utf-8
# ranger: Browse your files inside the terminal.
# -----------------------------------------------------------------------------

# An embedded shell script. Assuming this file is /usr/bin/ranger,
# this hack allows you to use the cd-after-exit feature by typing:
#   source ranger ranger
# Now when you quit ranger, it should change the directory of the
# parent shell to where you have last been in ranger.
# Works with at least bash and zsh.
#
# A convenient way of using this feature is adding this line to your bashrc:
#   alias rn='source ranger ranger'
# or, if ranger is not installed properly:
#   alias rn='source /path/to/ranger.py /path/to/ranger.py'
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


# Importing of the main method may fail if the ranger directory
# neither is in the same directory as this file, nor in one of
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

