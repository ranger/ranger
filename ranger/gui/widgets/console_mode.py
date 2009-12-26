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
