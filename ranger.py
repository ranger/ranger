#!/usr/bin/python
# coding=utf-8
# ranger: Browse your files inside the terminal.


# An embedded shell script. Assuming this file is /usr/bin/ranger,
# this hack allows you to use the cd-after-exit feature by typing:
# source ranger ranger
# Now when you quit ranger, it should change the directory of the
# parent shell to where you have last been in ranger.
# Works with at least bash and zsh.
"""":
if [ $1 ]; then
	cd "`$1 --cd-after-exit $@ 3>&1 1>&2 2>&3 3>&-`"
else
	echo "usage: source path/to/ranger.py path/to/ranger.py"
fi
return 1
"""

__doc__ = """Ranger - file browser for the unix terminal"""

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

