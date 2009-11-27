def initialize_commands(command_list):
	from ranger.fm import FM

	cl = command_list
	
	# note: the bound function will be called with one parameter, which
	# is the FM instance. To use functions with multiple parameters, use:
	# lambda fm: myfunction(fm, param1, param2, ...) as the function

	cl.bind(FM.move_left, 'h', 'back')
	cl.bind(FM.move_right, 'l', 'forward')
	cl.bind(FM.exit, 'q')

	cl.rebuild_paths()

