# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
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
Functions to escape metacharacters of arguments for shell commands.
"""

META_CHARS = (' ', "'", '"', '`', '&', '|', ';',
		'$', '!', '(', ')', '[', ']', '<', '>', '\t')
UNESCAPABLE = set(map(chr, list(range(9)) + list(range(10, 32)) \
		+ list(range(127, 256))))
META_DICT = dict([(mc, '\\' + mc) for mc in META_CHARS])

def shell_quote(string):
	"""Escapes by quoting"""
	return "'" + str(string).replace("'", "'\\''") + "'"

def shell_escape(arg):
	"""Escapes by adding backslashes"""
	arg = str(arg)
	if UNESCAPABLE & set(arg):
		return shell_quote(arg)
	arg = arg.replace('\\', '\\\\') # make sure this comes at the start
	for k, v in META_DICT.items():
		arg = arg.replace(k, v)
	return arg
