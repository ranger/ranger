import curses
from curses.ascii import ctrl, ESC

def initialize_commands(command_list):
	from ranger.actions import Actions as do
	from ranger.container.bookmarks import ALLOWED_KEYS as ALLOWED_BOOKMARK_KEYS

	def bind(fnc, *keys):
		command_list.bind(fnc, *keys)

	# syntax for binding keys: bind(fnc, *keys)
	# fnc is a function which is called with the FM instance,
	# keys are one or more key-combinations which are either:
	# * a string
	# * an integer which represents an ascii code
	# * a tuple of integers

	def curry(fnc, *args, **keywords):
		return lambda fm: fnc(fm, *args, **keywords)
	c=curry

	def move(**keywords):
		return lambda fm: fm.move_pointer(**keywords)

	def move_pages(n):
		return lambda fm: fm.move_pointer_by_pages(n)

	bind(do.move_left,               'h', curses.KEY_BACKSPACE, 127)
	bind(do.move_right,              'l')
	bind(c(do.move_right, mode=1),   curses.KEY_ENTER, ctrl('j'))
	bind(c(do.history_go, -1),       'H')
	bind(c(do.history_go,  1),       'L')
	bind(move( relative = 1 ),       'j')
	bind(move_pages( 0.5 ),          'J')
	bind(move( relative = -1 ),      'k')
	bind(move_pages( -0.5 ),         'K')
	bind(move( absolute = 0 ),       'gg')
	bind(move( absolute = -1 ),      'G')
	bind(do.edit_file,               'E')

	# toggle options
	def toggle_option(string):
		return lambda fm: fm.toggle_boolean_option(string)

	bind(toggle_option('show_hidden'),       'th')
	bind(toggle_option('preview_files'),     'tp')
	bind(toggle_option('directories_first'), 'td')

	# key combinations which change the current directory
	def cd(path):
		return lambda fm: fm.enter_dir(path)

	bind(cd("~"),          'gh')
	bind(cd("/etc"),       'ge')
	bind(cd("/usr"),       'gu')
	bind(cd("/"),          'gr')
	bind(cd("/media"),     'gm')
	bind(cd("/mnt"),       'gn')
	bind(cd("~/.trash"),   'gt')
	bind(cd("/srv"),       'gs')

	bind(do.search_forward,  'n')
	bind(do.search_backward, 'N')

	# bookmarks
	for key in ALLOWED_BOOKMARK_KEYS:
		bind(c(do.enter_bookmark, key),   "`" + key, "'" + key)
		bind(c(do.set_bookmark, key),     "m" + key)
		bind(c(do.unset_bookmark, key),   "um" + key)

	# system functions
	bind(do.exit,         ctrl('D'), 'q', 'ZZ')
	bind(do.reset,        ctrl('R'))
	bind(do.redraw,       ctrl('L'))
	bind(do.interrupt,    ctrl('C'))
	bind(do.resize,       curses.KEY_RESIZE)
	bind(do.handle_mouse, curses.KEY_MOUSE)
	bind(curry(do.open_console, ':'), ':')
	bind(curry(do.open_console, '/'), '/')
	bind(curry(do.open_console, '!'), '!')
	bind(curry(do.open_console, '@'), 'r')

	def test(fm):
		from ranger.helper import log
		log(fm.bookmarks.dct)
	bind(test, 'x')

	command_list.rebuild_paths()


def initialize_console_commands(command_list):
	from ranger.actions import Actions as do
	from ranger.gui.wconsole import WConsole

	def bind(fnc, *keys):
		command_list.bind(fnc, *keys)

	def type_key(key):
		return lambda con, fm: con.type_key(key)

	def curry(fnc, *args, **keywords):
		return lambda con, fm: fnc(con, *args, **keywords)

	def curry_fm(fnc, *args, **keywords):
		return lambda con, fm: fnc(fm, *args, **keywords)
	c_fm = curry_fm
	c = curry

	# movement
	bind(c(WConsole.move, relative = -1), curses.KEY_LEFT, ctrl('b'))
	bind(c(WConsole.move, relative =  1), curses.KEY_RIGHT, ctrl('f'))
	bind(c(WConsole.move, absolute = 0), curses.KEY_HOME, ctrl('a'))
	bind(c(WConsole.move, absolute = -1), curses.KEY_END, ctrl('e'))
	bind(c(WConsole.delete, 0), curses.KEY_DC, ctrl('d'))
	bind(c(WConsole.delete, -1), curses.KEY_BACKSPACE, 127, ctrl('h'))
	bind(c(WConsole.delete_rest, -1), ctrl('U'))
	bind(c(WConsole.delete_rest,  1), ctrl('K'))

	# system functions
	bind(c(WConsole.close),    ESC, ctrl('C'))
	bind(WConsole.execute,  curses.KEY_ENTER, ctrl('j'))
	bind(c_fm(do.redraw), ctrl('L'))
	bind(c_fm(do.resize), curses.KEY_RESIZE)

	for i in range(ord(' '), ord('~')):
		bind(type_key(i), i)

	command_list.rebuild_paths()
