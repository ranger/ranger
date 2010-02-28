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

DEFAULT = 0
COMMAND = 1
COMMAND_QUICK = 2
OPEN = 3
OPEN_QUICK = 4
SEARCH = 5

def is_valid_mode(mode):
	"""
	Returns True or False depending on whether the mode is valid or not.
	"""
	return isinstance(mode, int) and mode >= 0 and mode <= 5

def all_modes(mode):
	"""
	Returns a generator containing all valid modes.
	"""
	return range(6)

def mode_to_class(mode):
	"""
	Associates modes with the actual classes
	from ranger.gui.widgets.console.
	"""
	from .console import Console, CommandConsole, OpenConsole, \
			QuickOpenConsole, QuickCommandConsole, SearchConsole

	if mode == DEFAULT:
		return Console
	if mode == COMMAND:
		return CommandConsole
	if mode == OPEN:
		return OpenConsole
	if mode == OPEN_QUICK:
		return QuickOpenConsole
	if mode == COMMAND_QUICK:
		return QuickCommandConsole
	if mode == SEARCH:
		return SearchConsole
	raise ValueError
