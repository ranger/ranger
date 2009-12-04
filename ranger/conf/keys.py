def initialize_commands(cl):
	from ranger.fm import FM
	from curses.ascii import ctrl
	import curses

	# syntax for binding keys: cl.bind(fnc, *keys)
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

	cl.bind(FM.move_left,               'h', curses.KEY_BACKSPACE, 127)
	cl.bind(FM.move_right,              'l')
	cl.bind(c(FM.move_right, mode=1),   curses.KEY_ENTER, ctrl('j'))
	cl.bind(c(FM.history_go, -1),       'H')
	cl.bind(c(FM.history_go,  1),       'L')
	cl.bind(move( relative = 1 ),       'j')
	cl.bind(move_pages( 0.5 ),          'J')
	cl.bind(move( relative = -1 ),      'k')
	cl.bind(move_pages( -0.5 ),         'K')
	cl.bind(move( absolute = 0 ),       'gg')
	cl.bind(move( absolute = -1 ),      'G')
	cl.bind(FM.edit_file,               'E')

	# toggle options
	def toggle_option(string):
		return lambda fm: fm.toggle_boolean_option(string)

	cl.bind(toggle_option('show_hidden'),       'th')
	cl.bind(toggle_option('preview_files'),     'tp')
	cl.bind(toggle_option('directories_first'), 'td')

	# key combinations which change the current directory
	def cd(path):
		return lambda fm: fm.enter_dir(path)

	cl.bind(cd("~"),          'gh')
	cl.bind(cd("/etc"),       'ge')
	cl.bind(cd("/usr"),       'gu')
	cl.bind(cd("/"),          'gr')
	cl.bind(cd("/media"),     'gm')
	cl.bind(cd("/mnt"),       'gn')
	cl.bind(cd("~/.trash"),   'gt')
	cl.bind(cd("/srv"),       'gs')

	# system functions
	cl.bind(FM.exit,         ctrl('D'), 'q', 'ZZ')
	cl.bind(FM.reset,        ctrl('R'))
	cl.bind(FM.redraw,       ctrl('L'))
	cl.bind(FM.interrupt,    ctrl('C'))
	cl.bind(FM.resize,       curses.KEY_RESIZE)
	cl.bind(FM.handle_mouse, curses.KEY_MOUSE)
	cl.bind(curry(FM.open_console, ':'), ':')
	cl.bind(curry(FM.open_console, '/'), '/')
	cl.bind(curry(FM.open_console, '!'), '!')
	cl.bind(curry(FM.open_console, '@'), 'r')

	cl.rebuild_paths()


def initialize_console_commands(cl):
	from ranger.fm import FM
	from ranger.gui.wconsole import WConsole
	from curses.ascii import ctrl, ESC
	import curses

	def type_key(key):
		return lambda con, fm: con.type_key(key)

	def curry(fnc, *args, **keywords):
		return lambda con, fm: fnc(con, *args, **keywords)

	def curry_fm(fnc, *args, **keywords):
		return lambda con, fm: fnc(fm, *args, **keywords)
	c_fm = curry_fm
	c = curry

	# movement
	cl.bind(c(WConsole.move, relative = -1), curses.KEY_LEFT, ctrl('b'))
	cl.bind(c(WConsole.move, relative =  1), curses.KEY_RIGHT, ctrl('f'))
	cl.bind(c(WConsole.move, absolute = 0), curses.KEY_HOME, ctrl('a'))
	cl.bind(c(WConsole.move, absolute = -1), curses.KEY_END, ctrl('e'))
	cl.bind(c(WConsole.delete, 0), curses.KEY_DC, ctrl('d'))
	cl.bind(c(WConsole.delete, -1), curses.KEY_BACKSPACE, 127, ctrl('h'))
	cl.bind(c(WConsole.delete_rest, -1), ctrl('U'))
	cl.bind(c(WConsole.delete_rest,  1), ctrl('K'))

	# system functions
	cl.bind(c(WConsole.close),    ESC, ctrl('C'))
	cl.bind(WConsole.execute,  curses.KEY_ENTER, ctrl('j'))
	cl.bind(c_fm(FM.redraw), ctrl('L'))
	cl.bind(c_fm(FM.resize), curses.KEY_RESIZE)

	for i in range(ord(' '), ord('~')):
		cl.bind(type_key(i), i)

