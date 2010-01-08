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
