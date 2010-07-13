from ranger.slim.fs import File, Directory, npath
import os.path
import curses
from os.path import join, dirname

class Status(object):
	dircache = {}
	bookmarks = {}
	selection = []
	curses_is_on = False
	keybuffer = None
	draw_bookmarks = False
	cwd = None
	ls_l_mode = False

	def exit(self):
		raise SystemExit()

	def move(self, position):
		self.cwd.pointer = position
		self.sync_pointer()

	def sync_pointer(self):
		self.cwd.sync_pointer(self.stdscr.getmaxyx()[0] - 2)

	def reload(self):
		self.stdscr.addstr(0, self.stdscr.getmaxyx()[1] - 10, "loading..")
		self.stdscr.refresh()
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

	def load_bookmarks(self):
		self.bookmarks = {}
		f = open('/home/hut/.ranger/bookmarks', 'r')
		for line in f:
			if len(line) > 1 and line[1] == ':':
				self.bookmarks[line[0]] = line[2:-1]
		f.close()

	def save_bookmarks(self):
		f = open('/home/hut/.ranger/bookmarks', 'w')
		for key, val in self.bookmarks.items():
			f.write(''.join((key, ':', val, '\n')))
		f.close()

	def enter_bookmark(self, key):
		self.load_bookmarks()
		try:
			self.cd(self.bookmarks[key])
		except KeyError:
			pass

	def set_bookmark(self, key, val):
		self.load_bookmarks()
		self.bookmarks[key] = val
		self.save_bookmarks()

	def select_file(self, fname, single_directory=True):
		if single_directory and self.selection \
				and dirname(self.selection[0]) != dirname(fname):
			self.selection = [fname]
		elif fname not in self.selection:
			self.selection.append(fname)

	def unselect_file(self, fname):
		if fname in self.selection:
			self.selection.remove(fname)

	def toggle_select_file(self, fname, single_directory=True):
		if fname in self.selection:
			self.selection.remove(fname)
		else:
			self.select_file(fname, single_directory=single_directory)

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

	def cd(self, path, bookmark=True):
		path = npath(path, cwd=(self.cwd.path if self.cwd else '.'))
		try:
			os.chdir(path)
		except:
			return
		if bookmark:
			self.bookmarks["'"] = self.cwd.path
			self.save_bookmarks()
		self.cwd = self.get_dir(path, normalpath=True)
		self._build_pathway(path)
		self._set_pointers_for_backview()

	def get_dir(self, path, normalpath=False):
		if self.cwd:
			path = npath(path, self.cwd.path)
		else:
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
			if result and result.is_dir:
				return self.get_dir(result.path)

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
