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

	def move(**keywords):
		return lambda fm: fm.move_pointer(**keywords)

	def move_pages(n):
		return lambda fm: fm.move_pointer_by_pages(n)

	def toggle_option(string):
		return lambda fm: fm.toggle_boolean_option(string)

	def cd(path):
		return lambda fm: fm.enter_dir(path)

	cl.bind(FM.move_left,           'h', curses.KEY_BACKSPACE, 127)
	cl.bind(FM.move_right,          'l', curses.KEY_ENTER, ctrl('j'))
	cl.bind(move( relative = 1 ),   'j')
	cl.bind(move_pages( 0.5 ),      'J')
	cl.bind(move( relative = -1 ),  'k')
	cl.bind(move_pages( -0.5 ),     'K')
	cl.bind(move( absolute = 0 ),   'gg')
	cl.bind(move( absolute = -1 ),  'G')
	cl.bind(FM.edit_file,           'E')

	# toggle options
	cl.bind(toggle_option('show_hidden'),       'th')
	cl.bind(toggle_option('preview_files'),     'tp')
	cl.bind(toggle_option('directories_first'), 'td')

	# key combinations which change the current directory
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
	cl.bind(FM.resize,       curses.KEY_RESIZE)
	cl.bind(FM.handle_mouse, curses.KEY_MOUSE)

	cl.rebuild_paths()

