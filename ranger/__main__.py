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
import ranger

def parse_arguments():
	"""Parse the program arguments"""

	from optparse import OptionParser, SUPPRESS_HELP
	from ranger.ext.openstruct import OpenStruct
	from ranger import __version__, USAGE, DEFAULT_CONFDIR

	parser = OptionParser(usage=USAGE, version='ranger ' + __version__)

	parser.add_option('-d', '--debug', action='store_true',
			help="activate debug mode")
	parser.add_option('-c', '--clean', action='store_true',
			help="don't touch/require any config files. ")
	parser.add_option('-r', '--confdir', type='string',
			metavar='dir', default=DEFAULT_CONFDIR,
			help="the configuration directory. (%default)")
	parser.add_option('-m', '--mode', type='int', default=0, metavar='n',
			help="if a filename is supplied, run it with this mode")
	parser.add_option('-f', '--flags', type='string', default='',
			metavar='string',
			help="if a filename is supplied, run it with these flags.")

	options, positional = parser.parse_args()
	arg = OpenStruct(options.__dict__, targets=positional)
	arg.confdir = os.path.expanduser(arg.confdir)

	return arg


def load_settings(fm, clean):
	import ranger.api.commands
	if not clean:
		try:
			os.makedirs(ranger.arg.confdir)
		except OSError as err:
			if err.errno != 17:  # 17 means it already exists
				print("This configuration directory could not be created:")
				print(ranger.arg.confdir)
				print("To run ranger without the need for configuration")
				print("files, use the --clean option.")
				raise SystemExit()

		sys.path[0:0] = [ranger.arg.confdir]

		# Load commands
		comcont = ranger.api.commands.CommandContainer()
		ranger.api.commands.alias = comcont.alias
		try:
			import commands
			comcont.load_commands_from_module(commands)
		except ImportError:
			pass
		from ranger.defaults import commands
		comcont.load_commands_from_module(commands)
		commands = comcont

		# Load apps
		try:
			import apps
		except ImportError:
			from ranger.defaults import apps

		# Load keys
		from ranger import shared, api
		from ranger.api import keys
		keymanager = shared.EnvironmentAware.env.keymanager
		keys.keymanager = keymanager
		from ranger.defaults import keys
		try:
			import keys
		except ImportError:
			pass
		del sys.path[0]
	else:
		comcont = ranger.api.commands.CommandContainer()
		ranger.api.commands.alias = comcont.alias
		from ranger.defaults import commands, keys, apps
		comcont.load_commands_from_module(commands)
		commands = comcont
	fm.commands = commands
	fm.keys = keys
	fm.apps = apps.CustomApplications()


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

	from ranger.ext import curses_interrupt_handler
	from ranger.core.fm import FM
	from ranger.core.environment import Environment
	from ranger.shared import (EnvironmentAware, FileManagerAware,
			SettingsAware)
	from ranger.gui.defaultui import DefaultUI as UI
	from ranger.fsobject.file import File

	# Ensure that a utf8 locale is set.
	if getdefaultlocale()[1] not in ('utf8', 'UTF-8'):
		for locale in ('en_US.utf8', 'en_US.UTF-8'):
			try: setlocale(LC_ALL, locale)
			except: pass
			else: break
		else: setlocale(LC_ALL, '')
	else: setlocale(LC_ALL, '')

	arg = parse_arguments()
	ranger.arg = arg

	if not ranger.arg.debug:
		curses_interrupt_handler.install_interrupt_handler()

	SettingsAware._setup()

	if arg.targets:
		target = arg.targets[0]
		if not os.access(target, os.F_OK):
			print("File or directory doesn't exist: %s" % target)
			sys.exit(1)
		elif os.path.isfile(target):
			thefile = File(target)
			fm = FM()
			load_settings(fm, ranger.arg.clean)
			fm.execute_file(thefile, mode=arg.mode, flags=arg.flags)
			sys.exit(0)
		else:
			path = target
	else:
		path = '.'

	try:
		# Initialize objects
		EnvironmentAware._assign(Environment(path))
		fm = FM()
		load_settings(fm, ranger.arg.clean)
		FileManagerAware._assign(fm)
		fm.ui = UI()

		# Run the file manager
		fm.initialize()
		fm.ui.initialize()
		fm.loop()
	finally:
		# Finish, clean up
		try:
			fm.ui.destroy()
		except (AttributeError, NameError):
			pass


if __name__ == '__main__':
	top_dir = os.path.dirname(sys.path[0])
	sys.path.insert(0, top_dir)
	main()
