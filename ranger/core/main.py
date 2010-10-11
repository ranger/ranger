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

"""
The main function responsible to initialize the FM object and stuff.
"""

from ranger.core.helper import *

def main():
	"""initialize objects and run the filemanager"""
	import locale
	import os.path
	import ranger
	from ranger.ext import curses_interrupt_handler
	from ranger.core.runner import Runner
	from ranger.core.fm import FM
	from ranger.core.environment import Environment
	from ranger.gui.defaultui import DefaultUI as UI
	from ranger.fsobject import File
	from ranger.core.shared import (EnvironmentAware, FileManagerAware,
			SettingsAware)

	try:
		locale.setlocale(locale.LC_ALL, '')
	except:
		print("Warning: Unable to set locale.  Expect encoding problems.")

	if not 'SHELL' in os.environ:
		os.environ['SHELL'] = 'bash'

	ranger.arg = arg = parse_arguments()
	if arg.copy_config:
		fm = FM()
		fm.copy_config_files()
		return 0

	SettingsAware._setup(clean=arg.clean)

	targets = arg.targets or ['.']
	target = targets[0]
	if arg.targets:
		if target.startswith('file://'):
			target = target[7:]
		if not os.access(target, os.F_OK):
			print("File or directory doesn't exist: %s" % target)
			sys.exit(1)
		elif os.path.isfile(target):
			def print_function(string):
				print(string)
			runner = Runner(logfunc=print_function)
			load_apps(runner, arg.clean)
			runner(files=[File(target)], mode=arg.mode, flags=arg.flags)
			sys.exit(1 if arg.fail_unless_cd else 0)

	crash_traceback = None
	try:
		# Initialize objects
		EnvironmentAware.env = Environment(target)
		fm = FM()
		fm.tabs = dict((n+1, os.path.abspath(path)) for n, path \
				in enumerate(targets[:9]))
		load_settings(fm, arg.clean)
		if fm.env.username == 'root':
			fm.settings.preview_files = False
		FileManagerAware.fm = fm
		fm.ui = UI()
		if not arg.debug:
			curses_interrupt_handler.install_interrupt_handler()

		# Run the file manager
		fm.initialize()
		fm.ui.initialize()
		fm.loop()
	except Exception:
		import traceback
		crash_traceback = traceback.format_exc()
	except SystemExit as error:
		return error.args[0]
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
			return 1
		return 0
