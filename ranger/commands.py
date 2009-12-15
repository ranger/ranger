import os

from ranger.shared import FileManagerAware

# -------------------------------- helper classes

class parse(object):
	def __init__(self, line):
		self.line = line
		self.chunks = line.split()

		try:
			self.firstpart = line[:line.rindex(' ') + 1]
		except ValueError:
			self.firstpart = ''

	def __add__(self, newpart):
		return self.firstpart + newpart

class Command(FileManagerAware):
	name = None
	def __init__(self, line):
		self.line = line

	def execute(self):
		pass

	def tab(self):
		pass

	def _no_change(self):
		return (self.line for i in range(100))

# -------------------------------- definitions

class cd(Command):
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

# -------------------------------- rest

by_name = {}
for varname, var in vars().copy().items():
	try:
		if issubclass(var, Command) and var != Command:
			by_name[var.name or varname] = var
	except TypeError:
		pass

def execute(name, line):
	try:
		command = by_name[name](line)
	except KeyError:
		pass
	else:
		command.execute()

def tab(name, line):
	try:
		command = by_name[name](line)
	except KeyError:
		pass
	else:
		return command.tab()

