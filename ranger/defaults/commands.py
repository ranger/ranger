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
from ranger.shared import FileManagerAware
from ranger.gui.widgets import console_mode as cmode
from ranger.ext.command_parser import LazyParser as parse

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

	def quick_open(self):
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
			# are we after a directory?
			if rel_dest.endswith('/') or rel_dest == '':
				_, dirnames, _ = os.walk(abs_dest).next()

			# are we in the middle of the filename?
			else:
				_, dirnames, _ = os.walk(abs_dirname).next()
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
				return line + join(rel_dirname, dirnames[0]) + '/'

			# more than one result. append no slash, so the user can
			# manually type in the slash to advance into that directory
			return (line + join(rel_dirname, dirname) for dirname in dirnames)

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
			# are we after a directory?
			if rel_dest.endswith('/') or rel_dest == '':
				_, dirnames, filenames = os.walk(abs_dest).next()
				names = dirnames + filenames

			# are we in the middle of the filename?
			else:
				_, dirnames, filenames = os.walk(abs_dirname).next()
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
				return line + join(rel_dirname, names[0]) + '/'

			# more than one result. append no slash, so the user can
			# manually type in the slash to advance into that directory
			return (line + join(rel_dirname, name) for name in names)


# -------------------------------- definitions

class cd(Command):
	"""
	:cd <dirname>

	The cd command changes the directory.
	The command 'cd -' is equivalent to typing ``.

	In the quick console, the directory will be entered without the
	need to press enter, as soon as there is one unambiguous match.
	"""

	def execute(self):
		line = parse(self.line)
		try:
			destination = line.rest(1)
		except IndexError:
			destination = '~'

		if destination == '-':
			self.fm.enter_bookmark('`')
		else:
			self.fm.cd(destination)

	def tab(self):
		return self._tab_only_directories()

	def quick_open(self):
		from os.path import isdir, join, normpath
		line = parse(self.line)
		cwd = self.fm.env.cwd.path

		rel_dest = line.rest(1)
		if not rel_dest:
			return False

		abs_dest = normpath(join(cwd, rel_dest))
		return rel_dest != '.' and isdir(abs_dest)


class find(Command):
	"""
	:find <string>

	The find command will attempt to find a partial, case insensitive
	match in the filenames of the current directory.

	In the quick command console, once there is one unambiguous match,
	the file will be run automatically.
	"""

	count = 0
	tab = Command._tab_directory_content

	def execute(self):
		if self.mode != cmode.COMMAND_QUICK:
			self._search()

		import re
		search = parse(self.line).rest(1)
		search = re.escape(search)
		self.fm.env.last_search = re.compile(search, re.IGNORECASE)

		if self.count == 1:
			self.fm.move_right()
			self.fm.block_input(0.5)

	def quick_open(self):
		self._search()
		if self.count == 1:
			return True

	def _search(self):
		self.count = 0
		line = parse(self.line)
		cwd = self.fm.env.cwd
		try:
			arg = line.rest(1)
		except IndexError:
			return False

		deq = deque(cwd.files)
		deq.rotate(-cwd.pointer)
		i = 0
		for fsobj in deq:
			filename = fsobj.basename_lower
			if arg in filename:
				self.count += 1
				if self.count == 1:
					cwd.move(absolute=(cwd.pointer + i) % len(cwd.files))
					self.fm.env.cf = cwd.pointed_obj
			if self.count > 1:
				return False
			i += 1

		return self.count == 1


class quit(Command):
	"""
	:quit

	Quits the program immediately.
	"""

	def execute(self):
		raise SystemExit


class delete(Command):
	"""
	:delete

	Tries to delete the selection.

	"Selection" is defined as all the "marked files" (by default, you
	can mark files with space or v). If there are no marked files,
	use the "current file" (where the cursor is)

	When attempting to delete non-empty directories or multiple
	marked files, it will require a confirmation: The last word in
	the line has to start with a 'y'.  This may look like:
	:delete yes
	:delete seriously? yeah!
	"""

	allow_abbrev = False
	WARNING = 'delete seriously? '

	def execute(self):
		line = parse(self.line)
		lastword = line.chunk(-1)

		if lastword.startswith('y'):
			# user confirmed deletion!
			return self.fm.delete()
		elif self.line.startswith(delete.WARNING):
			# user did not confirm deletion
			return

		cwd = self.fm.env.cwd
		cf = self.fm.env.cf

		if cwd.marked_items or \
		(cf.is_directory and not cf.empty() and not cf.islink):
			# better ask for a confirmation, when attempting to
			# delete multiple files or a non-empty directory.
			return self.fm.open_console(self.mode, delete.WARNING)

		# no need for a confirmation, just delete
		self.fm.delete()

class mkdir(Command):
	"""
	:mkdir <dirname>

	Creates a directory with the name <dirname>.
	"""

	def execute(self):
		from os.path import join, expanduser, lexists
		from os import mkdir

		line = parse(self.line)
		dirname = join(self.fm.env.cwd.path, expanduser(line.rest(1)))
		if not lexists(dirname):
			mkdir(dirname)
		else:
			self.fm.notify("file/directory exists!", bad=True)


class touch(Command):
	"""
	:touch <fname>

	Creates a file with the name <fname>.
	"""

	def execute(self):
		from os.path import join, expanduser, lexists
		from os import mkdir

		line = parse(self.line)
		fname = join(self.fm.env.cwd.path, expanduser(line.rest(1)))
		if not lexists(fname):
			open(fname, 'a')
		else:
			self.fm.notify("file/directory exists!", bad=True)


class edit(Command):
	"""
	:edit <filename>

	Opens the specified file in vim
	"""

	def execute(self):
		line = parse(self.line)
		self.fm.edit_file(line.rest(1))

	def tab(self):
		return self._tab_directory_content()


class eval_(Command):
	"""
	:eval <python code>

	Evaluates the python code.
	`fm' is a reference to the FM instance.
	To display text, use the function `p'.

	Examples:
	:eval fm
	:eval len(fm.env.directories)
	:eval p("Hello World!")
	"""
	name = 'eval'

	def execute(self):
		code = parse(self.line).rest(1)
		fm = self.fm
		p = fm.notify
		try:
			try:
				result = eval(code)
			except SyntaxError:
				exec(code)
			else:
				if result:
					p(result)
		except Exception as err:
			p(err)


class rename(Command):
	"""
	:rename <newname>

	Changes the name of the currently highlighted file to <newname>
	"""

	def execute(self):
		from ranger.fsobject.file import File
		line = parse(self.line)
		if not line.rest(1):
			return self.fm.notify('Syntax: rename <newname>', bad=True)
		self.fm.rename(self.fm.env.cf, line.rest(1))
		f = File(line.rest(1))
		self.fm.env.cwd.pointed_obj = f
		self.fm.env.cf = f

	def tab(self):
		return self._tab_directory_content()


class chmod(Command):
	"""
	:chmod <octal number>

	Sets the permissions of the selection to the octal number.

	The octal number is between 0 and 777. The digits specify the
	permissions for the user, the group and others.

	A 1 permits execution, a 2 permits writing, a 4 permits reading.
	Add those numbers to combine them. So a 7 permits everything.
	"""

	def execute(self):
		line = parse(self.line)
		mode = line.rest(1)

		try:
			mode = int(mode, 8)
			if mode < 0 or mode > 511:
				raise ValueError
		except ValueError:
			self.fm.notify("Need an octal number between 0 and 777!", bad=True)
			return

		for file in self.fm.env.get_selection():
			try:
				os.chmod(file.path, mode)
			except Exception as ex:
				self.fm.notify(ex)

		try:
			# reloading directory.  maybe its better to reload the selected
			# files only.
			self.fm.env.cwd.load_content()
		except:
			pass


class filter(Command):
	"""
	:filter <string>

	Displays only the files which contain <string> in their basename.
	"""

	def execute(self):
		line = parse(self.line)
		self.fm.set_filter(line.rest(1))


class grep(Command):
	"""
	:grep <string>

	Looks for a string in all marked files or directories
	"""

	def execute(self):
		line = parse(self.line)
		if line.rest(1):
			action = ['grep', '--color=always', '--line-number']
			action.extend(['-e', line.rest(1), '-r'])
			action.extend(f.path for f in self.fm.env.get_selection())
			self.fm.execute_command(action, flags='p')


# -------------------------------- rest

by_name = {}
for varname, var in vars().copy().items():
	try:
		if issubclass(var, Command) and var != Command:
			by_name[var.name or varname] = var
	except TypeError:
		pass
del varname
del var

def alias(**kw):
	"""Create an alias for commands, eg: alias(quit=exit)"""
	for key, value in kw.items():
		by_name[key] = value

def get_command(name, abbrev=True):
	if abbrev:
		lst = [cls for cmd, cls in by_name.items() \
				if cmd.startswith(name) \
				and cls.allow_abbrev \
				or cmd == name]
		if len(lst) == 0:
			raise KeyError
		if len(lst) == 1 or by_name[name] in lst:
			return lst[0]
		raise ValueError("Ambiguous command")
	else:
		try:
			return by_name[name]
		except KeyError:
			return None

def command_generator(start):
	return (cmd + ' ' for cmd in by_name if cmd.startswith(start))

alias(e=edit)  # to make :e unambiguous.

