# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
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
	import sys
	from ranger.core.shared import (EnvironmentAware, FileManagerAware,
			SettingsAware)
	from ranger.core.fm import FM

	if not sys.stdin.isatty():
		sys.stderr.write("Error: Must run ranger from terminal\n")
		raise SystemExit(1)

	try:
		locale.setlocale(locale.LC_ALL, '')
	except:
		print("Warning: Unable to set locale.  Expect encoding problems.")

	# so that programs can know that ranger spawned them:
	level = 'RANGER_LEVEL'
	if level in os.environ and os.environ[level].isdigit():
		os.environ[level] = str(int(os.environ[level]) + 1)
	else:
		os.environ[level] = '1'

	if not 'SHELL' in os.environ:
		os.environ['SHELL'] = 'bash'

	ranger.arg = arg = parse_arguments()
	if arg.copy_config is not None:
		fm = FM()
		fm.copy_config_files(arg.copy_config)
		return 1 if arg.fail_unless_cd else 0
	if arg.list_tagged_files:
		fm = FM()
		try:
			f = open(fm.confpath('tagged'), 'r')
		except:
			pass
		else:
			for line in f.readlines():
				if len(line) > 2 and line[1] == ':':
					if line[0] in arg.list_tagged_files:
						sys.stdout.write(line[2:])
				elif len(line) > 0 and '*' in arg.list_tagged_files:
					sys.stdout.write(line)
		return 1 if arg.fail_unless_cd else 0

	SettingsAware._setup(clean=arg.clean)

	if arg.selectfile:
		arg.selectfile = os.path.abspath(arg.selectfile)
		arg.targets.insert(0, os.path.dirname(arg.selectfile))

	targets = arg.targets or ['.']
	target = targets[0]
	if arg.targets:
		if target.startswith('file://'):
			target = target[7:]
		if not os.access(target, os.F_OK):
			print("File or directory doesn't exist: %s" % target)
			return 1
		elif os.path.isfile(target):
			def print_function(string):
				print(string)
			from ranger.core.runner import Runner
			from ranger.fsobject import File
			fm = FM()
			runner = Runner(logfunc=print_function, fm=fm)
			load_apps(runner, arg.clean)
			runner(files=[File(target)], mode=arg.mode, flags=arg.flags)
			return 1 if arg.fail_unless_cd else 0

	crash_traceback = None
	try:
		# Initialize objects
		from ranger.core.environment import Environment
		fm = FM()
		FileManagerAware.fm = fm
		EnvironmentAware.env = Environment(target)
		fm.tabs = dict((n+1, os.path.abspath(path)) for n, path \
				in enumerate(targets[:9]))
		load_settings(fm, arg.clean)

		if arg.list_unused_keys:
			from ranger.ext.keybinding_parser import (special_keys,
					reversed_special_keys)
			maps = fm.env.keymaps['browser']
			for key in sorted(special_keys.values(), key=lambda x: str(x)):
				if key not in maps:
					print("<%s>" % reversed_special_keys[key])
			for key in range(33, 127):
				if key not in maps:
					print(chr(key))
			return 1 if arg.fail_unless_cd else 0

		if fm.env.username == 'root':
			fm.settings.preview_files = False
			fm.settings.use_preview_script = False
		if not arg.debug:
			from ranger.ext import curses_interrupt_handler
			curses_interrupt_handler.install_interrupt_handler()

		if arg.selectfile:
			fm.select_file(arg.selectfile)

		# Run the file manager
		fm.initialize()
		fm.ui.initialize()

		if arg.cmd:
			for command in arg.cmd:
				fm.execute_console(command)

		if ranger.arg.profile:
			import cProfile
			import pstats
			profile = None
			ranger.__fm = fm
			cProfile.run('ranger.__fm.loop()', '/tmp/ranger_profile')
			profile = pstats.Stats('/tmp/ranger_profile', stream=sys.stderr)
		else:
			fm.loop()
	except Exception:
		import traceback
		crash_traceback = traceback.format_exc()
	except SystemExit as error:
		return error.args[0]
	finally:
		if crash_traceback:
			try:
				filepath = fm.env.cf.path if fm.env.cf else "None"
			except:
				filepath = "None"
		try:
			fm.ui.destroy()
		except (AttributeError, NameError):
			pass
		if ranger.arg.profile and profile:
			profile.strip_dirs().sort_stats('cumulative').print_callees()
		if crash_traceback:
			print("ranger version: %s, executed with python %s" %
					(ranger.__version__, sys.version.split()[0]))
			print("Locale: %s" % '.'.join(str(s) for s in locale.getlocale()))
			try:
				print("Current file: %s" % filepath)
			except:
				pass
			print(crash_traceback)
			print("ranger crashed.  " \
				"Please report this traceback at:")
			print("http://savannah.nongnu.org/bugs/?group=ranger&func=additem")
			return 1
		return 0
