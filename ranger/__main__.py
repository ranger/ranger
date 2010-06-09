#!/usr/bin/env python
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

# Most import statements in this module are inside the functions.
# This enables more convenient exception handling in ranger.py
# (ImportError will imply that this module can't be found)
# convenient exception handling in ranger.py (ImportError)

import os
import sys

def parse_arguments():
	"""Parse the program arguments"""
	from optparse import OptionParser, SUPPRESS_HELP
	from ranger import __version__, USAGE, DEFAULT_CONFDIR
	from ranger.ext.openstruct import OpenStruct
	parser = OptionParser(usage=USAGE, version='ranger ' + __version__)

	parser.add_option('-d', '--debug', action='store_true',
			help="activate debug mode")
	parser.add_option('-c', '--clean', action='store_true',
			help="don't touch/require any config files. ")
	parser.add_option('--fail-if-run', action='store_true', # COMPAT
			help=SUPPRESS_HELP)
	parser.add_option('--fail-unless-cd', action='store_true',
			help="experimental: return the exit code 1 if ranger is" \
					"used to run a file (with `ranger filename`)")
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
	if arg.fail_if_run:
		arg.fail_unless_cd = arg.fail_if_run
		del arg['fail_if_run']

	return arg


def allow_access_to_confdir(confdir, allow):
	if allow:
		try:
			os.makedirs(confdir)
		except OSError as err:
			if err.errno != 17:  # 17 means it already exists
				print("This configuration directory could not be created:")
				print(confdir)
				print("To run ranger without the need for configuration")
				print("files, use the --clean option.")
				raise SystemExit()
		if not confdir in sys.path:
			sys.path[0:0] = [confdir]
	else:
		if sys.path[0] == confdir:
			del sys.path[0]


def load_settings(fm, clean):
	import ranger.shared
	import ranger.api.commands
	import ranger.api.keys
	if not clean:
		allow_access_to_confdir(ranger.arg.confdir, True)

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
		keymanager = ranger.shared.EnvironmentAware.env.keymanager
		ranger.api.keys.keymanager = keymanager
		from ranger.defaults import keys
		try:
			import keys
		except ImportError:
			pass
		# COMPAT WARNING
		if hasattr(keys, 'initialize_commands'):
			print("Warning: the syntax for ~/.ranger/keys.py has changed.")
			print("Your custom keys are not loaded."\
					"  Please update your configuration.")
		allow_access_to_confdir(ranger.arg.confdir, False)
	else:
		comcont = ranger.api.commands.CommandContainer()
		ranger.api.commands.alias = comcont.alias
		from ranger.api import keys
		keymanager = ranger.shared.EnvironmentAware.env.keymanager
		ranger.api.keys.keymanager = keymanager
		from ranger.defaults import commands, keys, apps
		comcont.load_commands_from_module(commands)
		commands = comcont
	fm.commands = commands
	fm.keys = keys
	fm.apps = apps.CustomApplications()


def load_apps(fm, clean):
	import ranger
	if not clean:
		allow_access_to_confdir(ranger.arg.confdir, True)
		try:
			import apps
		except ImportError:
			from ranger.defaults import apps
		allow_access_to_confdir(ranger.arg.confdir, False)
	else:
		from ranger.defaults import apps
	fm.apps = apps.CustomApplications()


def main():
	"""initialize objects and run the filemanager"""
	try:
		import curses
	except ImportError as errormessage:
		print(errormessage)
		print('ranger requires the python curses module. Aborting.')
		sys.exit(1)
	import locale
	import ranger
	from ranger.ext import curses_interrupt_handler
	from ranger.core.runner import Runner
	from ranger.core.fm import FM
	from ranger.core.environment import Environment
	from ranger.gui.defaultui import DefaultUI as UI
	from ranger.fsobject import File
	from ranger.shared import (EnvironmentAware, FileManagerAware,
			SettingsAware)

	try: locale.setlocale(locale.LC_ALL, '')
	except: print("Warning: Unable to set locale.  Expect encoding problems.")

	if not 'SHELL' in os.environ:
		os.environ['SHELL'] = 'bash'

	arg = parse_arguments()
	ranger.arg = arg

	if not ranger.arg.debug:
		curses_interrupt_handler.install_interrupt_handler()

	SettingsAware._setup()

	if arg.targets:
		target = arg.targets[0]
		if target.startswith('file://'):
			target = target[7:]
		if not os.access(target, os.F_OK):
			print("File or directory doesn't exist: %s" % target)
			sys.exit(1)
		elif os.path.isfile(target):
			def print_function(string):
				print(string)
			runner = Runner(logfunc=print_function)
			load_apps(runner, ranger.arg.clean)
			runner(files=[File(target)], mode=arg.mode, flags=arg.flags)
			sys.exit(1 if arg.fail_unless_cd else 0)
		else:
			path = target
	else:
		path = '.'

	crash_traceback = None
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
	except Exception:
		import traceback
		crash_traceback = traceback.format_exc()
	finally:
		try:
			fm.ui.destroy()
		except (AttributeError, NameError):
			pass
		if crash_traceback:
			print(crash_traceback)
			print("Ranger crashed.  " \
					"Please report this (including the traceback) at:")
			print("http://savannah.nongnu.org/bugs/?group=ranger&func=additem")


if __name__ == '__main__':
	# The ranger directory can be executed directly, for example by typing
	# python /usr/lib/python2.6/site-packages/ranger
	sys.path.insert(0, os.path.dirname(sys.path[0]))
	main()
