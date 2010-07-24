# -*- coding: utf-8 -*-
# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
# This software is licensed under the GNU GPLv3; see COPYING for details.
from pithy.status import Status
from pithy.gui import ui
from pithy.fs import File, Directory, npath
from pithy.communicate import data_dir, conf_dir
import curses
import locale
import optparse
import os
import pwd
import socket

def main():
	try:
		locale.setlocale(locale.LC_ALL, '')
	except:
		print("Warning: Unable to set locale.  Expect encoding problems.")
	global status
	status = Status()
	File.status = status
	status.username = pwd.getpwuid(os.geteuid()).pw_name
	status.hostname = socket.gethostname()

	# Parse arguments
	parser = optparse.OptionParser(usage='pithy [options] [path]')
	parser.add_option('-n', '--no-defaults', action='store_true',
			help="don't load the default settings, only the custom" \
					" configuration at ~/.config/pithy/rc.py.")
	parser.add_option('-r', '--reset', action='store_true',
			help="if using shell integration, discard previous status.")
	options, positional = parser.parse_args()
	origin = npath(positional[0]) if positional else os.getcwd()
	status.origin = origin

	# Load the RC file
	if not options.no_defaults:
		rc_file = os.sep.join([data_dir(), 'settings.py'])
		exec(compile(open(rc_file).read(), rc_file, 'exec'), globals())
	try:
		rc_file = os.sep.join([conf_dir(), 'rc.py'])
		rc = compile(open(rc_file).read(), rc_file, 'exec')
	except IOError:
		pass
	else:
		exec(rc, globals())

	# Initialize pithy
	status.change_cwd(origin)
	try:
		status.stdscr = curses.initscr()
		if not options.reset:
			status.load_status()
		status.curses_on()
		ui(status)
	except KeyboardInterrupt:
		pass
	except SystemExit as e:
		return e.code
	finally:
		status.curses_off()
		status.save_status()
	return 0
