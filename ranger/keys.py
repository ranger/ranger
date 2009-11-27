def initialize_commands(command_list):
	from ranger.fm import FM
	from curses.ascii import ctrl

	cl = command_list
	
	# syntax for binding keys: cl.bind(fnc, *keys)
	# fnc is a function which is called with the FM instance,
	# keys are one or more key-combinations which are either:
	# * a string
	# * an integer which represents an ascii value
	# * a tuple of integers

	def move(relative = 0, absolute = None):
		return lambda fm: fm.move_pointer(relative = relative, absolute = absolute)

	def move_screens(n):
		return lambda fm: fm.move_pointer_by_screensize(n)

	cl.bind(FM.move_left, 'h', 195, 'back')
	cl.bind(FM.move_right, 'l', 'forward')
	cl.bind(move( relative = 1 ), 'j')
	cl.bind(move_screens( 0.5 ), 'J')
	cl.bind(move( relative = -1 ), 'k')
	cl.bind(move_screens( -0.5 ), 'K')
	cl.bind(move( absolute = 0 ), 'gg')
	cl.bind(move( absolute = -1 ), 'G')
	cl.bind(FM.exit, 'q', ctrl('D'), 'ZZ')
	cl.bind(FM.redraw, ctrl('L'))

	cl.rebuild_paths()

