#!/usr/bin/python
# coding=utf-8

# An embedded shell script. Assuming this file is /usr/bin/ranger,
# this hack allows you to use the cd-after-exit feature by typing:
# source ranger ranger
"""":
if [ $1 ]; then
	cd "`$1 --cd-after-exit $@ 3>&1 1>&2 2>&3 3>&-`"
else
	echo "use with: source path/to/ranger.py path/to/ranger.py"
fi
return 1
"""

import sys, os

# Change the directory of the parent shell after exiting Ranger.
# Read the comments in wrapper.sh for more info.
try:
	assert sys.argv[1] == '--cd-after-exit'
	cd_after_exit = True
	sys.stderr = sys.stdout
	del sys.argv[1]
except:
	cd_after_exit = False

from ranger import debug, fm, options, environment, command, keys
from ranger.defaultui import DefaultUI as UI

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

	finally:
		if cd_after_exit:
			try: sys.__stderr__.write(env.pwd.path)
			except: pass

if __name__ == "__main__": main()
