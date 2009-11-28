def initialize_commands(command_list):
	from ranger.fm import FM
	from curses.ascii import ctrl
	import curses

	cl = command_list
	
	# syntax for binding keys: cl.bind(fnc, *keys)
	# fnc is a function which is called with the FM instance,
	# keys are one or more key-combinations which are either:
	# * a string
	# * an integer which represents an ascii value
	# * a tuple of integers

	def move(relative = 0, absolute = None):
		return lambda fm: fm.move_pointer(
				relative = relative, absolute = absolute)

	def move_pages(n):
		return lambda fm: fm.move_pointer_by_pages(n)

	def toggle_option(string):
		return lambda fm: fm.toggle_boolean_option(string)

	def cd(path):
		return lambda fm: fm.enter_dir(path)

	cl.bind(FM.move_left, 'h', 195, 'back')
	cl.bind(FM.move_right, 'l', 'forward')
	cl.bind(move( relative = 1 ), 'j')
	cl.bind(move_pages( 0.5 ), 'J')
	cl.bind(move( relative = -1 ), 'k')
	cl.bind(move_pages( -0.5 ), 'K')
	cl.bind(move( absolute = 0 ), 'gg')
	cl.bind(move( absolute = -1 ), 'G')

	cl.bind(toggle_option('show_hidden'), 'th')


	gX = {
			'h': '~',
			'e': '/etc',
			'u': '/usr',
			'r': '/',
			'm': '/media',
			'n': '/mnt',
			't': '~/.trash',
			's': '/srv',
			}

	for x, path in gX.items():
		cl.bind( cd(path), 'g' + x )

#	cl.bind(cd("~"), 'gh')
#	cl.bind(cd("/etc"), 'ge')
#	cl.bind(cd("/usr"), 'gu')
#	cl.bind(cd("/"), 'gr')
#	cl.bind(cd("/media"), 'gm')
#	cl.bind(cd("/mnt"), 'gn')
#	cl.bind(cd("~/.trash"), 'gt')
#	cl.bind(cd("/srv"), 'gs')

	cl.bind(FM.exit, 'q', ctrl('D'), 'ZZ')
	cl.bind(FM.reset, ctrl('R'))
	cl.bind(FM.redraw, ctrl('L'))
	cl.bind(FM.resize, curses.KEY_RESIZE)

	cl.rebuild_paths()

