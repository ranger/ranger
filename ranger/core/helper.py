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

"""Helper functions"""

from errno import EEXIST
import os.path
import sys
from ranger import *

def parse_arguments():
	"""Parse the program arguments"""
	from optparse import OptionParser
	from ranger import __version__
	from ranger.ext.openstruct import OpenStruct
	from os.path import expanduser

	if 'XDG_CONFIG_HOME' in os.environ and os.environ['XDG_CONFIG_HOME']:
		default_confdir = os.environ['XDG_CONFIG_HOME'] + '/ranger'
	else:
		default_confdir = CONFDIR

	parser = OptionParser(usage=USAGE, version='ranger %s%s' \
			% (__version__, " (stable)" if STABLE else ""))

	parser.add_option('-d', '--debug', action='store_true',
			help="activate debug mode")
	parser.add_option('-c', '--clean', action='store_true',
			help="don't touch/require any config files. ")
	parser.add_option('--copy-config', type='string', metavar='which',
			help="copy the default configs to the local config directory. "
			"Possible values: all, rc, apps, commands, options, scope")
	parser.add_option('--fail-unless-cd', action='store_true',
			help="experimental: return the exit code 1 if ranger is" \
					"used to run a file (with `ranger filename`)")
	parser.add_option('-r', '--confdir', type='string',
			metavar='dir', default=default_confdir,
			help="the configuration directory. (%default)")
	parser.add_option('-m', '--mode', type='int', default=0, metavar='n',
			help="if a filename is supplied, run it with this mode")
	parser.add_option('-f', '--flags', type='string', default='',
			metavar='string',
			help="if a filename is supplied, run it with these flags.")
	parser.add_option('--choosefile', type='string', metavar='TARGET',
			help="Makes ranger act like a file chooser. When opening "
			"a file, it will quit and write the name of the selected "
			"file to TARGET.")
	parser.add_option('--choosefiles', type='string', metavar='TARGET',
			help="Makes ranger act like a file chooser for multiple files "
			"at once. When opening a file, it will quit and write the name "
			"of all selected files to TARGET.")
	parser.add_option('--choosedir', type='string', metavar='TARGET',
			help="Makes ranger act like a directory chooser. When ranger quits"
			", it will write the name of the last visited directory to TARGET")
	parser.add_option('--list-unused-keys', action='store_true',
			help="List common keys which are not bound to any action.")
	parser.add_option('--selectfile', type='string', metavar='filepath',
			help="Open ranger with supplied file selected.")
	parser.add_option('--list-tagged-files', type='string', default=None,
			metavar='tag',
			help="List all files which are tagged with the given tag, default: *")
	parser.add_option('--profile', action='store_true',
			help="Print statistics of CPU usage on exit.")
	parser.add_option('--cmd', action='append', type='string', metavar='COMMAND',
			help="Execute COMMAND after the configuration has been read. "
			"Use this option multiple times to run multiple commands.")

	options, positional = parser.parse_args()
	arg = OpenStruct(options.__dict__, targets=positional)
	arg.confdir = expanduser(arg.confdir)

	return arg


def load_settings(fm, clean):
	from ranger.core.actions import Actions
	import ranger.core.shared
	import ranger.api.commands
	from ranger.defaults import commands

	# Load default commands
	fm.commands = ranger.api.commands.CommandContainer()
	exclude = ['settings']
	include = [name for name in dir(Actions) if name not in exclude]
	fm.commands.load_commands_from_object(fm, include)
	fm.commands.load_commands_from_module(commands)

	if not clean:
		allow_access_to_confdir(ranger.arg.confdir, True)

		# Load custom commands
		try:
			import commands
			fm.commands.load_commands_from_module(commands)
		except ImportError:
			pass

		# Load apps
		try:
			import apps
		except ImportError:
			from ranger.defaults import apps
		fm.apps = apps.CustomApplications()

		# Load rc.conf
		custom_conf = fm.confpath('rc.conf')
		default_conf = fm.relpath('defaults', 'rc.conf')
		load_default_rc = fm.settings.load_default_rc

		if load_default_rc:
			fm.source(default_conf)
		if os.access(custom_conf, os.R_OK):
			fm.source(custom_conf)

		# XXX Load plugins (experimental)
		try:
			plugindir = fm.confpath('plugins')
			plugins = [p[:-3] for p in os.listdir(plugindir) \
					if p.endswith('.py') and not p.startswith('_')]
		except:
			pass
		else:
			if not os.path.exists(fm.confpath('plugins', '__init__.py')):
				f = open(fm.confpath('plugins', '__init__.py'), 'w')
				f.close()

			ranger.fm = fm
			for plugin in sorted(plugins):
				try:
					module = __import__('plugins', fromlist=[plugin])
					fm.log.append("Loaded plugin '%s'." % module)
				except Exception as e:
					fm.log.append("Error in plugin '%s'" % plugin)
					import traceback
					for line in traceback.format_exception_only(type(e), e):
						fm.log.append(line)
			ranger.fm = None

		allow_access_to_confdir(ranger.arg.confdir, False)
	else:
		from ranger.defaults import apps
		fm.apps = apps.CustomApplications()
		fm.source(fm.relpath('defaults', 'rc.conf'))


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


def allow_access_to_confdir(confdir, allow):
	if allow:
		try:
			os.makedirs(confdir)
		except OSError as err:
			if err.errno != EEXIST:  # EEXIST means it already exists
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


# Debugging functions.  These will be activated when run with --debug.
# Example usage in the code:
# import ranger; ranger.log("hello world")
def log(*objects, **keywords):
	"""
	Writes objects to a logfile (for the purpose of debugging only.)
	Has the same arguments as print() in python3.
	"""
	from ranger import arg
	if LOGFILE is None or not arg.debug or arg.clean: return
	start = 'start' in keywords and keywords['start'] or 'ranger:'
	sep   =   'sep' in keywords and keywords['sep']   or ' '
	_file =  'file' in keywords and keywords['file']  or open(LOGFILE, 'a')
	end   =   'end' in keywords and keywords['end']   or '\n'
	_file.write(sep.join(map(str, (start, ) + objects)) + end)


def log_traceback():
	from ranger import arg
	if LOGFILE is None or not arg.debug or arg.clean: return
	import traceback
	traceback.print_stack(file=open(LOGFILE, 'a'))
