#!/usr/bin/python
# coding=utf-8

# An embedded shell script. Assuming this file is /usr/bin/ranger,
# this hack allows you to use the cd-after-exit feature by typing:
# source ranger ranger
# Now when you quit ranger, it should change the directory of the
# parent shell to where you have last been in ranger.
# Works with at least bash and zsh.
"""":
if [ $1 ]; then
	cd "`$1 --cd-after-exit $@ 3>&1 1>&2 2>&3 3>&-`"
else
	echo "use with: source path/to/ranger.py path/to/ranger.py"
fi
return 1
"""

from ranger.fm import FM
from ranger.environment import Environment
from ranger.command import CommandList
from ranger.conf import keys, options
from ranger.gui.defaultui import DefaultUI as UI
from ranger.conf.colorschemes.snow import Snow as ColorScheme

import sys, os, locale

try:
	assert sys.argv[1] == '--cd-after-exit'
	cd_after_exit = True
	sys.stderr = sys.stdout
	del sys.argv[1]
except:
	cd_after_exit = False

# TODO: Parse arguments

# TODO: load config

os.stat_float_times(True)
locale.setlocale(locale.LC_ALL, 'en_US.utf8')

try:
	path = os.path.abspath('.')
	opt = options.dummy()

	env = Environment(opt)
	commandlist = CommandList()
	colorscheme = ColorScheme()
	keys.initialize_commands(commandlist)

	my_ui = UI(env, commandlist, colorscheme)
	my_fm = FM(env)
	my_fm.feed(path, my_ui)
	my_fm.run()

finally:
	try:
		my_ui.exit()
	except:
		pass

	if cd_after_exit:
		try:
			sys.__stderr__.write(env.pwd.path)
		except:
			pass

