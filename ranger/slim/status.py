from ranger.slim.fs import File, Directory
import os.path
from os.path import join, abspath, expanduser

def npath(path):
	if path[0] == '~':
		return abspath(expanduser(path))
	return abspath(path)

class Status(object):
	dircache = {}

	def exit(self):
		raise SystemExit()

	def move(self, position):
		self.cwd.pointer = position

	def cd(self, path):
		path = npath(path)
		try:
			os.chdir(path)
		except:
			return
		self.cwd = self.get_dir(path, normalpath=True)

		# build the pathway, a tuple of directory objects which lie
		# on the path to the current directory.
		if path == '/':
			self.pathway = (self.get_dir('/'), )
		else:
			pathway = []
			currentpath = '/'
			for dir in path.split('/'):
				currentpath = join(currentpath, dir)
				pathway.append(self.get_dir(currentpath))
			self.pathway = tuple(pathway)

	def get_dir(self, path, normalpath=False):
		path = npath(path)
		try:
			return self.dircache[path]
		except:
			obj = Directory(path, None)
			self.dircache[path] = obj
			return obj

	def get_level(self, level):
		if level == 0:
			return self.cwd
		if level < 0:
			try:
				return self.pathway[level - 1]
			except IndexError:
				return None
		if level == 1:
			result = self.cwd.current_file
			if os.path.isdir(result.path):
				return self.get_dir(result.path)
