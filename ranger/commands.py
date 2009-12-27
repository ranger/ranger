import os
from ranger.shared import FileManagerAware
from ranger.gui.widgets import console_mode as cmode
from ranger.ext.command_parser import LazyParser as parse

class Command(FileManagerAware):
	"""Abstract command class"""
	name = None
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
		pwd = self.fm.env.pwd.path

		try:
			rel_dest = line.rest(1)
		except IndexError:
			rel_dest = ''

		# expand the tilde into the user directory
		if rel_dest.startswith('~'):
			return line + expanduser(rel_dest) + '/'

		# define some shortcuts
		abs_dest = join(pwd, rel_dest)
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
		pwd = self.fm.env.pwd.path

		try:
			rel_dest = line.rest(1)
		except IndexError:
			rel_dest = ''

		# expand the tilde into the user directory
		if rel_dest.startswith('~'):
			return line + expanduser(rel_dest) + '/'

		# define some shortcuts
		abs_dest = join(pwd, rel_dest)
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
	The cd command changes the directory. The command 'cd -' is
	equivalent to typing ``. In the quick console, the directory
	will be entered without the need to press enter, as soon as there
	is one unambiguous match.
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
			self.fm.enter_dir(destination)

	def tab(self):
		return self._tab_only_directories()
	
	def quick_open(self):
		from os.path import isdir, join, normpath
		line = parse(self.line)
		pwd = self.fm.env.pwd.path

		try:
			rel_dest = line.rest(1)
		except IndexError:
			return False

		abs_dest = normpath(join(pwd, rel_dest))
		return rel_dest != '.' and isdir(abs_dest)

class find(Command):
	"""
	The find command will attempt to find a partial, case insensitive
	match in the filenames of the current directory. In the quick command
	console, once there is one unambiguous match, the file will be run
	automatically.
	"""
	count = 0
	def execute(self):
		if self.mode != cmode.COMMAND_QUICK:
			self._search()

		import re
		search = parse(self.line).rest(1)
		search = re.escape(search)
		self.fm.env.last_search = re.compile(search, re.IGNORECASE)

	def quick_open(self):
		self._search()
		if self.count == 1:
			self.fm.move_right()
			self.fm.block_input(0.5)
			return True

	def tab(self):
		return self._tab_directory_content()

	def _search(self):
		self.count = 0
		line = parse(self.line)
		pwd = self.fm.env.pwd
		try:
			arg = line.rest(1)
		except IndexError:
			return False
		
		length = len(pwd.files)
		for i in range(length):
			actual_index = (pwd.pointer + i) % length
			filename = pwd.files[actual_index].basename_lower
			if arg in filename:
				self.count += 1
				if self.count == 1:
					pwd.move(absolute=actual_index)
					self.fm.env.cf = pwd.pointed_obj
			if self.count > 1:
				return False

		return self.count == 1


class quit(Command):
	"""Quits the program."""
	def execute(self):
		raise SystemExit


class delete(Command):
	def execute(self):
		self.fm.delete()


class mkdir(Command):
	def execute(self):
		line = parse(self.line)
		try:
			self.fm.mkdir(line.rest(1))
		except IndexError:
			pass


class rename(Command):
	def execute(self):
		line = parse(self.line)
		self.fm.rename(self.fm.env.cf, line.rest(1))

	def tab(self):
		return self._tab_directory_content()
	

# -------------------------------- rest

by_name = {}
for varname, var in vars().copy().items():
	try:
		if issubclass(var, Command) and var != Command:
			by_name[var.name or varname] = var
	except TypeError:
		pass

def alias(**kw):
	for key, value in kw.items():
		by_name[key] = value

alias(q=quit)

def command_generator(start):
	return (cmd + ' ' for cmd in by_name if cmd.startswith(start))

