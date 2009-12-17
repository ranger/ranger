import os
from ranger.shared import FileManagerAware

# -------------------------------- helper classes

class parse(object):
	"""Parse commands and extract information"""
	def __init__(self, line):
		self.line = line
		self.chunks = line.split()

		try:
			self.firstpart = line[:line.rindex(' ') + 1]
		except ValueError:
			self.firstpart = ''

	def chunk(self, n, otherwise=''):
		if len(self.chunks) >= n:
			return self.chunks[n]
		else:
			return otherwise


	def __add__(self, newpart):
		return self.firstpart + newpart

class Command(FileManagerAware):
	"""Abstract command class"""
	name = None
	mode = ':'
	line = ''
	def __init__(self, line, mode):
		self.line = line
		self.mode = mode

	def execute(self):
		pass

	def tab(self):
		pass

	def quick_open(self):
		pass


# -------------------------------- definitions

class cd(Command):
	"""The cd command changes the directory. The command 'cd -' is
	equivalent to typing ``. In the quick console, the directory
	will be entered without the need to press enter, as soon as there
	is one unambiguous match.
	"""

	def execute(self):
		line = parse(self.line)
		try:
			destination = line.chunks[1]
		except IndexError:
			destination = '~'

		if destination == '-':
			self.fm.enter_bookmark('`')
		else:
			self.fm.enter_dir(destination)

	def tab(self):
		from os.path import dirname, basename, expanduser, join, isdir

		line = parse(self.line)
		pwd = self.fm.env.pwd.path

		try:
			rel_dest = line.chunks[1]
		except IndexError:
			rel_dest = ''

		if rel_dest.startswith('~'):
			return line + expanduser(rel_dest) + '/'

		abs_dest = join(pwd, rel_dest)
		abs_dirname = dirname(abs_dest)
		rel_basename = basename(rel_dest)
		rel_dirname = dirname(rel_dest)
		
		try:
			if rel_dest.endswith('/') or rel_dest == '':
				_, dirnames, _ = os.walk(abs_dest).next()
			else:
				_, dirnames, _ = os.walk(abs_dirname).next()
				dirnames = [dn for dn in dirnames \
						if dn.startswith(rel_basename)]
		except (OSError, StopIteration):
			pass
		else:
			dirnames.sort()

			if len(dirnames) == 0:
				return

			if len(dirnames) == 1:
				return line + join(rel_dirname, dirnames[0]) + '/'

			return (line + join(rel_dirname, dirname) for dirname in dirnames)
	
	def quick_open(self):
		from os.path import isdir, join, normpath
		line = parse(self.line)
		pwd = self.fm.env.pwd.path

		try:
			rel_dest = line.chunks[1]
		except IndexError:
			return False

		abs_dest = normpath(join(pwd, rel_dest))
		return rel_dest != '.' and isdir(abs_dest)

class find(Command):
	"""The find command will attempt to find a partial, case insensitive
	match in the filenames of the current directory. In the quick command
	console, once there is one unambiguous match, the file will be run
	automatically.
	"""
	count = 0
	def execute(self):
		if self.mode != '>':
			self._search()

		import re
		search = parse(self.line).chunk(1)
		search = re.escape(search)
		self.fm.env.last_search = re.compile(search, re.IGNORECASE)

	def quick_open(self):
		self._search()
		if self.count == 1:
			self.fm.move_right()
			self.fm.block_input(0.5)
			return True

	def _search(self):
		self.count = 0
		line = parse(self.line)
		pwd = self.fm.env.pwd
		try:
			arg = line.chunks[1]
		except IndexError:
			return False
		
		length = len(pwd.files)
		for i in range(length):
			actual_index = (pwd.pointed_index + i) % length
			filename = pwd.files[actual_index].basename_lower
			if arg in filename:
				self.count += 1
				if self.count == 1:
					pwd.move_pointer(absolute=actual_index)
					self.fm.env.cf = pwd.pointed_file
			if self.count > 1:
				return False

		return self.count == 1


class quit(Command):
	"""Quits the program."""
	def execute(self):
		raise SystemExit


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
