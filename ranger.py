#!/usr/bin/python -O
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

# Embed a script which allows you to change the directory of the parent shell
# after you exit ranger.  Run it with the command: source ranger ranger
"""":
if [ $1 ]; then
	$@ --fail-unless-cd &&
	if [ -z "$XDG_CONFIG_HOME" ]; then
		cd "$(grep \^\' ~/.config/ranger/bookmarks | cut -b3-)"
	else
		cd "$(grep \^\' "$XDG_CONFIG_HOME"/ranger/bookmarks | cut -b3-)"
	fi
else
	echo "usage: source path/to/ranger.py path/to/ranger.py"
fi
return 1
"""

# Set the actual docstring
__doc__ = """Ranger - file browser for the unix terminal"""

# Start ranger
import ranger.__main__
exit_code = ranger.__main__.main() 
raise SystemExit(exit_code)
