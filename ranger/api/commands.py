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
from collections import deque
from ranger.api import *
from ranger.shared import FileManagerAware
from ranger.gui.widgets import console_mode as cmode
from ranger.ext.command_parser import LazyParser as parse


class CommandContainer(object):
	def __init__(self):
		self.aliases = {}
		self.commands = {}

	def __getitem__(self, key):
		return self.commands[key]

	def alias(self, new, old):
		self.aliases[new] = old

	def load_commands_from_module(self, module):
		for varname, var in vars(module).items():
			try:
				if issubclass(var, Command) and var != Command:
					self.commands[var.name or varname] = var
			except TypeError:
				pass
		for new, old in self.aliases.items():
			try:
				self.commands[new] = self.commands[old]
			except:
				pass

	def get_command(self, name, abbrev=True):
		if abbrev:
			lst = [cls for cmd, cls in self.commands.items() \
					if cls.allow_abbrev and cmd.startswith(name) \
					or cmd == name]
			if len(lst) == 0:
				raise KeyError
			if len(lst) == 1:
				return lst[0]
			if self.commands[name] in lst:
				return self.commands[name]
			raise ValueError("Ambiguous command")
		else:
			try:
				return self.commands[name]
			except KeyError:
				return None

	def command_generator(self, start):
		return (cmd + ' ' for cmd in self.commands if cmd.startswith(start))


class Command(FileManagerAware):
	"""Abstract command class"""
	name = None
	allow_abbrev = True
	def __init__(self, line, mode):
		self.line = line
		self.mode = mode

	def execute(self):
		"""Override this"""

	def tab(self):
		"""Override this"""

	def quick(self):
		"""Override this"""

	def _tab_only_directories(self):
		from os.path import dirname, basename, expanduser, join, isdir

		line = parse(self.line)
		cwd = self.fm.env.cwd.path

		try:
			rel_dest = line.rest(1)
		except IndexError:
			rel_dest = ''

		# expand the tilde into the user directory
		if rel_dest.startswith('~'):
			rel_dest = expanduser(rel_dest)

		# define some shortcuts
		abs_dest = join(cwd, rel_dest)
		abs_dirname = dirname(abs_dest)
		rel_basename = basename(rel_dest)
		rel_dirname = dirname(rel_dest)

		try:
			# are we at the end of a directory?
			if rel_dest.endswith('/') or rel_dest == '':
				_, dirnames, _ = next(os.walk(abs_dest))

			# are we in the middle of the filename?
			else:
				_, dirnames, _ = next(os.walk(abs_dirname))
				dirnames = [dn for dn in dirnames \
						if dn.startswith(rel_basename)]
		except (OSError, StopIteration):
			# os.walk found nothing
			pass
		else:
			dirnames.sort()

			# no results, return None
			if len(dirnames) == 0:
				return

			# one result. since it must be a directory, append a slash.
			if len(dirnames) == 1:
				return line.start(1) + join(rel_dirname, dirnames[0]) + '/'

			# more than one result. append no slash, so the user can
			# manually type in the slash to advance into that directory
			return (line.start(1) + join(rel_dirname, dirname) for dirname in dirnames)

	def _tab_directory_content(self):
		from os.path import dirname, basename, expanduser, join, isdir

		line = parse(self.line)
		cwd = self.fm.env.cwd.path

		try:
			rel_dest = line.rest(1)
		except IndexError:
			rel_dest = ''

		# expand the tilde into the user directory
		if rel_dest.startswith('~'):
			rel_dest = expanduser(rel_dest)

		# define some shortcuts
		abs_dest = join(cwd, rel_dest)
		abs_dirname = dirname(abs_dest)
		rel_basename = basename(rel_dest)
		rel_dirname = dirname(rel_dest)

		try:
			# are we at the end of a directory?
			if rel_dest.endswith('/') or rel_dest == '':
				_, dirnames, filenames = next(os.walk(abs_dest))
				names = dirnames + filenames

			# are we in the middle of the filename?
			else:
				_, dirnames, filenames = next(os.walk(abs_dirname))
				names = [name for name in (dirnames + filenames) \
						if name.startswith(rel_basename)]
		except (OSError, StopIteration):
			# os.walk found nothing
			pass
		else:
			names.sort()

			# no results, return None
			if len(names) == 0:
				return

			# one result. since it must be a directory, append a slash.
			if len(names) == 1:
				return line.start(1) + join(rel_dirname, names[0]) + '/'

			# more than one result. append no slash, so the user can
			# manually type in the slash to advance into that directory
			return (line.start(1) + join(rel_dirname, name) for name in names)
