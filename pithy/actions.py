# -*- coding: utf-8 -*-
# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
# This software is licensed under the GNU GPLv3. See COPYING for details.
"""
The Action class contains methods for manipulating the status of pithy
and is used as a superclass for pithy.status.Status.
"""

import curses
import os.path
from pithy.fs import File, Directory, npath
from pithy.communicate import conf_dir, echo
from pithy.ext.shell_escape import shell_quote
from os.path import join, dirname, expanduser

class Actions(object):
	_curses_is_on = False
	_dircache = {}
	cwd = None
	selection = []

	def exit(self, exit_code=0):
		raise SystemExit(exit_code)

	def launch(self, command, gui_off=True):
		from pithy.ext.waitpid_no_intr import waitpid_no_intr
		import string
		import subprocess
		class _LaunchTemplate(string.Template):
			delimiter = '%'
			idpattern = '[sf]'
		if gui_off:
			self.curses_off()
		if _LaunchTemplate.delimiter in command:
			macros = {
				'f': shell_quote(self.cwd.current_file.path),
				's': ' '.join(shell_quote(f) for f in self.selection),
				'd': shell_quote(self.cwd.path),
			}
			command = _LaunchTemplate(command).safe_substitute(macros)
		process = subprocess.Popen(command, shell=True)
		waitpid_no_intr(process.pid)
		if gui_off:
			self.curses_on()

	def save_status(self):
		try:
			echo(self.cwd.path, 'directory')
			echo(self.cwd.current_file.path, 'pointer')
			echo(str(self.cwd.scroll_begin), 'scroll_start')
			echo('\n'.join(self.selection), 'marked')
		except:
			pass

	def load_status(self):
		try:
			pointer = os.environ['PITHY_POINTER']
		except:
			pass
		else:
			dir = self.get_dir(os.path.dirname(pointer))
			dir.select_filename(pointer)
		try:
			self.selection = os.environ['PITHY_MARKED'].split('\n')
		except:
			pass
		self.sync_pointer()

	def move(self, position):
		self.cwd.pointer = max(0, min(len(self.cwd.files) - 1, position))
		self.sync_pointer()

	def sync_pointer(self):
		self.cwd.sync_pointer(self.stdscr.getmaxyx()[0] - 2)

	def reload(self):
		self.stdscr.addstr(0, self.stdscr.getmaxyx()[1] - 10, "loading..")
		self.stdscr.refresh()
		old_cwd = self.cwd
		for key, val in self._dircache.items():
			del self._dircache[key]
		self._dircache = {}
		self.cwd = self.get_dir(old_cwd.path)
		self._build_pathway(old_cwd.path)
		self._set_pointers_for_backview()
		self.cwd.select_filename(old_cwd.current_file.path)
		self.cwd.scroll_begin = old_cwd.scroll_begin
		self.sync_pointer()
		self.hooks.reload_hook()

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
		self._curses_is_on = True

	def curses_off(self):
		self.stdscr.keypad(0)
		curses.echo()
		curses.nocbreak()
		curses.endwin()
		self._curses_is_on = False

	def cd(self, path):
		path = npath(path, cwd=(self.cwd.path if self.cwd else '.'))
		try:
			self.change_cwd(path)
		except OSError:
			return

	def change_cwd(self, path):
		os.chdir(path)
		self.cwd = self.get_dir(path)
		self._build_pathway(path)
		self._set_pointers_for_backview()

	def get_dir(self, path):
		if self.cwd:
			path = npath(path, self.cwd.path)
		else:
			path = npath(path)
		try:
			return self._dircache[path]
		except:
			obj = Directory(path, None)
			self._dircache[path] = obj
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
