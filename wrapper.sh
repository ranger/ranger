#!/bin/sh
#
# Use this file to activate a special feature:
# Changing the directory of the parent shell after exiting Ranger.
# To use this, create an alias for this command in your shell config:
#
# source path/to/wrapper.sh path/to/ranger.py
#
# (This does not work with all shells, it was successfully tested
# with bash and zsh though.)
#
if [ $1 ]; then
	cd "`$1 --cd-after-exit $@ 3>&1 1>&2 2>&3 3>&-`"
else
	echo "use with: source path/to/wrapper.sh path/to/ranger.py"
fi
