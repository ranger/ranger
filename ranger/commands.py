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
		line = parse(self.line)
		try:
			dest = line.chunks[1]
		except IndexError:
			dest = ''

		if dest.startswith('~'):
			return line + os.path.expanduser(dest) + '/'

		absolute = lambda path: os.path.join(self.fm.env.pwd.path, path)
		absdest = absolute(dest)

#		if dest == '':
#			return sorted(os.listdir(dest))

		if dest.endswith('/') or dest == '':
			if os.path.isdir(dest):
				walker = os.walk(absdest)
				_, dirnames, _ = walker.next()
				dirnames.sort()
				return (line.line + dirname for dirname in dirnames)

		try:
			original_dirname = os.path.dirname(absdest)
			basename = os.path.basename(absdest)

			walker = os.walk(original_dirname)
			_, dirnames, _ = walker.next()
			dirnames = [dn for dn in dirnames if dn.startswith(basename)]

			dirnames.sort()

			start = line + os.path.dirname(dest) + '/'
			if len(dirnames) == 0:
				return
			elif len(dirnames) == 1:
				if os.path.isdir(os.path.join(absdest, dirnames[0])):
					return start + dirnames[0] + '/'
				else:
					return start + dirnames[0]
			else:
				return (start + dirname for dirname in dirnames)
		except OSError:
			pass


# -------------------------------- rest

by_name = {}
for varname, var in vars().copy().items():
	try:
		if issubclass(var, Command) and var != Command:
			by_name[var.name or varname] = var
	except TypeError:
		pass

def execute(name, line):
	return by_name[name](line).execute()

def tab(name, line):
	return by_name[name](line).tab()
