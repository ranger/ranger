import sys
import os
from inspect import isclass, ismodule
from locale import setlocale, LC_ALL
from optparse import OptionParser, SUPPRESS_HELP

from ranger.fm import FM
from ranger.environment import Environment
from ranger.command import CommandList
from ranger.bookmark import Bookmarks
from ranger.conf import keys, options
from ranger.gui.defaultui import DefaultUI as UI
from ranger.gui.colorscheme import ColorScheme

VERSION = '1.0.0'

USAGE = '''%s [options] [path/filename]'''

def main():
	try:
		import curses
	except ImportError as errormessage:
		print(errormessage)
		print('ranger requires the python curses module. Aborting.')
		sys.exit(1)

	setlocale(LC_ALL, 'en_US.utf8')
	os.stat_float_times(True)

	# Parse options
	parser = OptionParser(
			usage = USAGE,
			version = 'ranger ' + VERSION )

	# Instead of using this directly, use the embedded
	# shell script by running ranger with:
	# source /path/to/ranger /path/to/ranger
	parser.add_option( '--cd-after-exit',
			action = 'store_true',
			dest = 'cd_after_exit',
			help = SUPPRESS_HELP )

	args, rest = parser.parse_args()

	if args.cd_after_exit:
		sys.stderr = sys.__stdout__
		if rest[0] == sys.argv[0]:
			del rest[0]
	
	# Initialize objects
	target = ' '.join(rest)
	if target:
		if not os.access(target, os.F_OK):
			print("File or directory doesn't exist: %s" % target)
			sys.exit(1)
		elif os.path.isfile(target):
			FM.execute_file(FM(0, 0), target)
			sys.exit(0)
		else:
			path = target

	else:
		path = '.'

	opt = options.dummy()

	# get colorscheme
	scheme = options.colorscheme
	if isclass(scheme) and issubclass(scheme, ColorScheme):
		colorscheme = scheme()

	elif ismodule(scheme):
		for var_name in dir(scheme):
			var = getattr(scheme, var_name)
			if var != ColorScheme and isclass(var) and\
					issubclass(var, ColorScheme):
				colorscheme = var()
				break
		else:
			print("The given colorscheme module contains no valid colorscheme!")
			sys.exit(1)

	else:
		print("Cannot locate colorscheme!")
		sys.exit(1)

	env = Environment(path, opt)
	commandlist = CommandList()
	keys.initialize_commands(commandlist)
	bookmarks = Bookmarks()
	bookmarks.load()

	my_ui = UI(env, commandlist, colorscheme)
	my_fm = FM(env, my_ui, bookmarks)

	try:
		# Run the file manager
		my_ui.initialize()
		my_fm.run()

	finally:
		# Finish, clean up
		my_ui.exit()

		if args.cd_after_exit:
			try: sys.__stderr__.write(env.pwd.path)
			except: pass
