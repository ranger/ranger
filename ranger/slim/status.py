from ranger.slim.fs import File, Directory, npath
import os.path
import curses
from os.path import join

class Status(object):
	dircache = {}
	curses_is_on = False

	def exit(self):
		raise SystemExit()

	def move(self, position):
		self.cwd.pointer = position
		self.sync()

	def sync(self):
		self.cwd.sync_pointer(self.stdscr.getmaxyx()[0] - 2)

	def reload(self):
		old_cwd = self.cwd
		for key, val in self.dircache.items():
			del val.files[:]
			del self.dircache[key]
		self.dircache = {}
		self.cwd = self.get_dir(old_cwd.path)
		self._build_pathway(old_cwd.path)
		self._set_pointers_for_backview()
		self.cwd.pointer = old_cwd.pointer
		self.cwd.scroll_begin = old_cwd.scroll_begin

	def curses_on(self):
		curses.noecho()
		curses.cbreak()
		curses.curs_set(0)
		self.stdscr.keypad(1)
		try: curses.start_color()
		except: pass
		curses.use_default_colors()
		self.curses_is_on = True

	def curses_off(self):
		self.stdscr.keypad(0)
		curses.echo()
		curses.nocbreak()
		curses.endwin()
		self.curses_is_on = False

	def cd(self, path):
		path = npath(path)
		try:
			os.chdir(path)
		except:
			return
		self.cwd = self.get_dir(path, normalpath=True)
		self._build_pathway(path)
		self._set_pointers_for_backview()

	def _build_pathway(self, path):
		if path == '/':
			self.pathway = (self.get_dir('/'), )
		else:
			pathway = []
			currentpath = '/'
			for dir in path.split('/'):
				currentpath = join(currentpath, dir)
				pathway.append(self.get_dir(currentpath))
			self.pathway = tuple(pathway)

	def _set_pointers_for_backview(self):
		last_dir = None
		for directory in reversed(self.pathway):
			if last_dir is None:
				last_dir = directory
				continue

			directory.select_filename(last_dir.path)
			last_dir = directory

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
