#!/usr/bin/python
# coding=utf-8

# TODO: cd after exit

from ranger import debug, fm, options, environment, command, keys
from ranger.defaultui import DefaultUI as UI

# TODO: find out the real name of this script and include files relative to here

# TODO: Parse arguments

# TODO: load config

def main():
	import locale, os
	os.stat_float_times(True)
	locale.setlocale(locale.LC_ALL, 'en_US.utf8')

	try:
		path = os.path.abspath('.')
		opt = options.dummy()
		env = environment.Environment(opt)
		commandlist = command.CommandList()
		keys.initialize_commands(commandlist)

		my_ui = UI(env, commandlist)
		my_fm = fm.FM(env)
		my_fm.feed(path, my_ui)
		my_fm.run()

	except BaseException as original_error:
		try: my_ui.exit()
		except: pass

		raise original_error

if __name__ == "__main__": main()
