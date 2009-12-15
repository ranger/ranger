import curses
from curses.ascii import ctrl, ESC, DEL
from ranger.gui.widgets.console import Console
from ranger.container.bookmarks import ALLOWED_KEYS as ALLOWED_BOOKMARK_KEYS

def do(method, *args, **kw):
	return lambda fm: getattr(fm, method)(*args, **kw)

# syntax for binding keys: bind(*keys, fnc)
# fnc is a function which is called with the FM instance,
# keys are one or more key-combinations which are either:
# * a string
# * an integer which represents an ascii code
# * a tuple of integers
#
# in initialize_console_commands, fnc is a function which is
# called with the console widget instance instead.

def initialize_commands(command_list):
	"""Initialize the commands for the main user interface"""

	def bind(*args):
		command_list.bind(args[-1], *args[:-1])

	bind('h', curses.KEY_BACKSPACE, DEL, do('move_left'))
	bind('l', do('move_right'))
	bind(curses.KEY_ENTER, ctrl('j'), do('move_right', mode=1))
	bind('H', do('history_go', -1))
	bind('L', do('history_go',  1))
	bind('j', do('move_pointer', relative = 1))
	bind('J', do('move_pointer_by_pages', 0.5))
	bind('k', do('move_pointer', relative = -1))
	bind('K', do('move_pointer_by_pages', -0.5))
	bind('gg', do('move_pointer', absolute = 0))
	bind('G', do('move_pointer', absolute = -1))
	bind('E', do('edit_file'))

	bind('th', do('toggle_boolean_option', 'show_hidden'))
	bind('tp', do('toggle_boolean_option', 'preview_files'))
	bind('td', do('toggle_boolean_option', 'directories_first'))

	# key combinations which change the current directory
	def cd(path):
		return lambda fm: fm.enter_dir(path)

	bind('gh', do('cd', '~'))
	bind('ge', do('cd', '/etc'))
	bind('gu', do('cd', '/usr'))
	bind('gr', do('cd', '/'))
	bind('gm', do('cd', '/media'))
	bind('gn', do('cd', '/mnt'))
	bind('gt', do('cd', '~/.trash'))
	bind('gs', do('cd', '/srv'))

	bind('n', do('search_forward'))
	bind('N', do('search_backward'))

	# bookmarks
	for key in ALLOWED_BOOKMARK_KEYS:
		bind("`" + key, "'" + key, do('enter_bookmark', key))
		bind("m" + key, do('set_bookmark', key))
		bind("um" + key, do('unset_bookmark', key))

	# system functions
	bind(ctrl('D'), 'q', 'ZZ', do('exit'))
	bind(ctrl('R'), do('reset'))
	bind(ctrl('L'), do('redraw'))
	bind(ctrl('C'), do('interrupt'))
	bind(curses.KEY_RESIZE, do('resize'))
	bind(curses.KEY_MOUSE, do('handle_mouse'))
	bind(':', do('open_console', ':'))
	bind('/', do('open_console', '/'))
	bind('!', do('open_console', '!'))
	bind('r', do('open_console', '@'))

	def test(fm):
		from ranger import log
		log(fm.bookmarks.dct)
	bind('x', test)

	command_list.rebuild_paths()


def initialize_console_commands(command_list):
	"""Initialize the commands for the console widget only"""

	def bind(*args):
		command_list.bind(args[-1], *args[:-1])

	def do_fm(method, *args, **kw):
		return lambda con: getattr(con.fm, method)(*args, **kw)

	# movement
	bind(ctrl('b'), curses.KEY_LEFT, do('move', relative = -1))
	bind(ctrl('f'), curses.KEY_RIGHT, do('move', relative = 1))
	bind(ctrl('a'), curses.KEY_HOME, do('move', absolute = 0))
	bind(ctrl('e'), curses.KEY_END, do('move', absolute = -1))
	bind(ctrl('d'), curses.KEY_DC, do('delete', 0))
	bind(ctrl('h'), curses.KEY_BACKSPACE, DEL, do('delete', -1))
	bind(ctrl('w'), do('delete_word'))
	bind(ctrl('k'), do('delete_rest', 1))
	bind(ctrl('u'), do('delete_rest', -1))

	# system functions
	bind(ctrl('c'), do('close'))
	bind(ctrl('j'), curses.KEY_ENTER, do('execute'))
	bind(ctrl('l'), do_fm('redraw'))
	bind(curses.KEY_RESIZE, do_fm('resize'))

	# type keys
	def type_key(key):
		return lambda con: con.type_key(key)

	for i in range(ord(' '), ord('~')):
		bind(i, type_key(i))

	command_list.rebuild_paths()
