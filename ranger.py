#!/usr/bin/python
# coding=utf-8
# ranger: Browse your files inside the console.


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
	echo "use with: source path/to/ranger.py path/to/ranger.py"
fi
return 1
"""

try:
	from ranger.main import main

except ImportError as errormessage:
	print(errormessage)
	print("To run an uninstalled copy of ranger,")
	print("launch ranger.py in the top directory.")

else:
	main()

