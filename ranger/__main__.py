#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys


def parse_arguments():
	"""Parse the program arguments"""

	from optparse import OptionParser, SUPPRESS_HELP
	from ranger.ext.openstruct import OpenStruct
	from ranger import __version__, USAGE, DEFAULT_CONFDIR

	parser = OptionParser(usage=USAGE, version='ranger ' + __version__)

	# Instead of using this directly, use the embedded
	# shell script by running ranger with:
	# source /path/to/ranger /path/to/ranger
	parser.add_option('--cd-after-exit',
			action='store_true',
			help=SUPPRESS_HELP)

	parser.add_option('-d', '--debug', action='store_true',
			help="activate debug mode")

	parser.add_option('-c', '--clean', action='store_true',
			help="don't touch/require any config files. ")

	parser.add_option('-r', '--confdir', dest='confdir', type='string',
			default=DEFAULT_CONFDIR,
			help="the configuration directory. (%default)")

	parser.add_option('-m', '--mode', type='int', dest='mode', default=0,
			help="if a filename is supplied, run it with this mode")

	parser.add_option('-f', '--flags', type='string', dest='flags', default='',
			help="if a filename is supplied, run it with these flags.")

	options, positional = parser.parse_args()

	arg = OpenStruct(options.__dict__, targets=positional)

	arg.confdir = os.path.expanduser(arg.confdir)

	if arg.cd_after_exit:
		sys.stderr = sys.__stdout__

	if not arg.clean:
		try:
			os.makedirs(arg.confdir)
		except OSError as err:
			if err.errno != 17:  # 17 means it already exists
				print("This configuration directory could not be created:")
				print(arg.confdir)
				print("To run ranger without the need for configuration files")
				print("use the --clean option.")
				raise SystemExit()

		sys.path.append(arg.confdir)

	return arg

def main():
	"""initialize objects and run the filemanager"""
	try:
		import curses
	except ImportError as errormessage:
		print(errormessage)
		print('ranger requires the python curses module. Aborting.')
		sys.exit(1)

	from signal import signal, SIGINT
	from locale import getdefaultlocale, setlocale, LC_ALL

	import ranger
	from ranger.ext import curses_interrupt_handler
	from ranger.core.fm import FM
	from ranger.core.environment import Environment
	from ranger.shared.settings import SettingsAware
	from ranger.gui.defaultui import DefaultUI as UI
	from ranger.fsobject.file import File

	# Ensure that a utf8 locale is set.
	if getdefaultlocale()[1] not in ('utf8', 'UTF-8'):
		for locale in ('en_US.utf8', 'en_US.UTF-8'):
			try: setlocale(LC_ALL, locale)
			except: pass  #sometimes there is none available though...
	else:
		setlocale(LC_ALL, '')

	arg = parse_arguments()
	ranger.arg = arg

	if not ranger.arg.debug:
		curses_interrupt_handler.install_interrupt_handler()

	SettingsAware._setup()

	# Initialize objects
	if arg.targets:
		target = arg.targets[0]
		if not os.access(target, os.F_OK):
			print("File or directory doesn't exist: %s" % target)
			sys.exit(1)
		elif os.path.isfile(target):
			thefile = File(target)
			FM().execute_file(thefile, mode=arg.mode, flags=arg.flags)
			sys.exit(0)
		else:
			path = target
	else:
		path = '.'

	Environment(path)

	try:
		my_ui = UI()
		my_fm = FM(ui=my_ui)
		my_fm.stderr_to_out = arg.cd_after_exit

		# Run the file manager
		my_fm.initialize()
		my_ui.initialize()
		my_fm.loop()
	finally:
		# Finish, clean up
		if 'my_ui' in vars():
			my_ui.destroy()
		if arg.cd_after_exit:
			try: sys.__stderr__.write(my_fm.env.cwd.path)
			except: pass

if __name__ == '__main__':
	top_dir = os.path.dirname(sys.path[0])
	sys.path.insert(0, top_dir)
	main()
