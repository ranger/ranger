# Copyright (c) 2009, 2010 hut <hut@lavabit.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import os
import shutil
from inspect import cleandoc

from ranger.shared import EnvironmentAware, SettingsAware
from ranger import fsobject
from ranger.gui.widgets import console_mode as cmode
from ranger.applications import run
from ranger.fsobject import File

class Actions(EnvironmentAware, SettingsAware):
	search_method = 'ctime'
	search_forward = False

	def search(self, order=None, forward=True):
		original_order = order
		if self.search_forward:
			direction = bool(forward)
		else:
			direction = not bool(forward)

		if order is None:
			order = self.search_method
		else:
			self.set_search_method(order=order)

		if order in ('search', 'tag'):
			if order == 'search':
				arg = self.env.last_search
				if arg is None:
					return False
				if hasattr(arg, 'search'):
					fnc = lambda x: arg.search(x.basename)
				else:
					fnc = lambda x: arg in x.basename
			elif order == 'tag':
				fnc = lambda x: x.realpath in self.tags

			return self.env.pwd.search_fnc(fnc=fnc, forward=forward)

		elif order in ('size', 'mimetype', 'ctime'):
			pwd = self.env.pwd
			if original_order is not None:
				lst = list(pwd.files)
				if order == 'size':
					fnc = lambda item: -item.size
				elif order == 'mimetype':
					fnc = lambda item: item.mimetype
				elif order == 'ctime':
					fnc = lambda item: -int(item.stat and item.stat.st_ctime)
				lst.sort(key=fnc)
				pwd.set_cycle_list(lst)
				return pwd.cycle(forward=None)

			return pwd.cycle(forward=forward)

	def set_search_method(self, order, forward=True):
		if order in ('search', 'tag', 'size', 'mimetype', 'ctime'):
			self.search_method = order
			self.search_forward = forward

	def resize(self):
		"""Update the size of the UI"""
		self.ui.update_size()

	def exit(self):
		"""Exit the program"""
		raise SystemExit()

	def enter_dir(self, path, remember=False):
		"""Enter the directory at the given path"""
		if remember:
			pwd = self.env.pwd
			result = self.env.enter_dir(path)
			self.bookmarks.remember(pwd)
			return result
		return self.env.enter_dir(path)

	def cd(self, path, remember=True):
		"""enter the directory at the given path, remember=True"""
		self.enter_dir(path, remember)

	def tag_toggle(self, movedown=None):
		try:
			toggle = self.tags.toggle
		except AttributeError:
			return

		sel = self.env.get_selection()
		toggle(*tuple(map(lambda x: x.realpath, sel)))

		if movedown is None:
			movedown = len(sel) == 1
		if movedown:
			self.move_pointer(relative=1)

		if hasattr(self.ui, 'redraw_main_column'):
			self.ui.redraw_main_column()
	
	def tag_remove(self, movedown=None):
		try:
			remove = self.tags.remove
		except AttributeError:
			return

		sel = self.env.get_selection()
		remove(*tuple(map(lambda x: x.realpath, sel)))

		if movedown is None:
			movedown = len(sel) == 1
		if movedown:
			self.move_pointer(relative=1)

		if hasattr(self.ui, 'redraw_main_column'):
			self.ui.redraw_main_column()

	def enter_bookmark(self, key):
		"""Enter the bookmark with the name <key>"""
		try:
			destination = self.bookmarks[key]
			pwd = self.env.pwd
			if destination.path != pwd.path:
				self.bookmarks.enter(key)
				self.bookmarks.remember(pwd)
		except KeyError:
			pass

	def set_bookmark(self, key):
		"""Set the bookmark with the name <key> to the current directory"""
		self.bookmarks[key] = self.env.pwd

	def unset_bookmark(self, key):
		"""Delete the bookmark with the name <key>"""
		self.bookmarks.delete(key)

	def move_left(self, narg=1):
		"""Enter the parent directory"""
		try:
			directory = os.path.join(*(['..'] * narg))
		except:
			return
		self.env.enter_dir(directory)
	
	def move_right(self, mode=0):
		"""Enter the current directory or execute the current file"""
		cf = self.env.cf
		sel = self.env.get_selection()

		if not self.env.enter_dir(cf):
			if sel:
				if self.execute_file(sel, mode=mode) is False:
					self.open_console(cmode.OPEN_QUICK)

	def history_go(self, relative):
		"""Move back and forth in the history"""
		self.env.history_go(relative)
	
	def handle_mouse(self):
		"""Handle mouse-buttons if one was pressed"""
		self.ui.handle_mouse()
	
	def display_command_help(self, console_widget):
		if not hasattr(self.ui, 'open_pager'):
			return

		try:
			command = console_widget._get_cmd_class()
		except:
			self.notify("Feature not available!", bad=True)
			return

		if not command:
			self.notify("Command not found!", bad=True)
			return

		if not command.__doc__:
			self.notify("Command has no docstring. Try using python without -OO",
					bad=True)
			return

		pager = self.ui.open_pager()
		lines = cleandoc(command.__doc__).split('\n')
		pager.set_source(lines)
	
	def display_help(self, topic='index', narg=None):
		if not hasattr(self.ui, 'open_pager'):
			return

		from ranger.help import get_help, get_help_by_index

		if narg is not None:
			help_text = get_help_by_index(narg)
		else:
			help_text = get_help(topic)

		pager = self.ui.open_pager()
		pager.markup = 'help'
		lines = help_text.split('\n')
		pager.set_source(lines)

	def display_log(self):
		if not hasattr(self.ui, 'open_pager'):
			return

		pager = self.ui.open_pager()
		if self.log:
			pager.set_source(["Message Log:"] + list(self.log))
		else:
			pager.set_source(["Message Log:", "No messages!"])
	
	def display_file(self):
		if not hasattr(self.ui, 'open_embedded_pager'):
			return

		try:
			f = open(self.env.cf.path, 'r')
		except:
			pass
		else:
			pager = self.ui.open_embedded_pager()
			pager.set_source(f)

	def execute_file(self, files, **kw):
		"""Execute a file.
		app is the name of a method in Applications, without the "app_"
		flags is a string consisting of applications.ALLOWED_FLAGS
		mode is a positive integer.
		Both flags and mode specify how the program is run."""

		if isinstance(files, set):
			files = list(files)
		elif type(files) not in (list, tuple):
			files = [files]

		return run(fm=self, files=list(files), **kw)

	def execute_command(self, cmd, **kw):
		return run(fm=self, action=cmd, **kw)
	
	def edit_file(self, file=None):
		"""Calls execute_file with the current file and app='editor'"""
		if file is None:
			file = self.env.cf
		elif isinstance(file, str):
			file = File(os.path.expanduser(file))
		if file is None:
			return
		self.execute_file(file, app = 'editor')

	def open_console(self, mode=':', string=''):
		"""Open the console if the current UI supports that"""
		if hasattr(self.ui, 'open_console'):
			self.ui.open_console(mode, string)

	def move_pointer(self, relative = 0, absolute = None, narg=None):
		"""Move the pointer down by <relative> or to <absolute>"""
		self.env.pwd.move(relative=relative,
				absolute=absolute, narg=narg)

	def move_pointer_by_pages(self, relative):
		"""Move the pointer down by <relative> pages"""
		self.env.pwd.move(relative=int(relative * self.env.termsize[0]))

	def move_pointer_by_percentage(self, relative=0, absolute=None, narg=None):
		"""Move the pointer down by <relative>% or to <absolute>%"""
		try:
			factor = len(self.env.pwd) / 100.0
		except:
			return

		if narg is not None:
			absolute = narg

		self.env.pwd.move(
				relative=int(relative * factor),
				absolute=int(absolute * factor))

	def scroll(self, relative):
		"""Scroll down by <relative> lines"""
		if hasattr(self.ui, 'scroll'):
			self.ui.scroll(relative)
			self.env.cf = self.env.pwd.pointed_obj

	def redraw_window(self):
		"""Redraw the window"""
		self.ui.redraw_window()

	def reset(self):
		"""Reset the filemanager, clearing the directory buffer"""
		old_path = self.env.pwd.path
		self.env.directories = {}
		self.enter_dir(old_path)

	def toggle_boolean_option(self, string):
		"""Toggle a boolean option named <string>"""
		if isinstance(self.env.settings[string], bool):
			self.env.settings[string] ^= True

	def sort(self, func=None, reverse=None):
		if reverse is not None:
			self.env.settings['reverse'] = bool(reverse)

		if func is not None:
			self.env.settings['sort'] = str(func)
	
	def force_load_preview(self):
		cf = self.env.cf
		if hasattr(cf, 'unload') and hasattr(cf, 'load_content'):
			cf.unload()
			cf.load_content()

	def reload_cwd(self):
		try:
			cwd = self.env.pwd
		except:
			pass
		cwd.unload()
		cwd.load_content()

	def set_filter(self, fltr):
		try:
			self.env.pwd.filter = fltr
		except:
			pass
	
	def notify(self, text, duration=4, bad=False):
		if isinstance(text, Exception):
			text = str(text)
			bad = True
		self.log.appendleft(text)
		if hasattr(self.ui, 'notify'):
			self.ui.notify(text, duration=duration, bad=bad)
	
	def mark(self, all=False, toggle=False, val=None, movedown=None):
		"""
		A wrapper for the directory.mark_xyz functions.

		Arguments:
		all - change all files of the current directory at once?
		toggle - toggle the marked-status?
		val - mark or unmark?
		"""

		if self.env.pwd is None:
			return

		pwd = self.env.pwd

		if movedown is None:
			movedown = not all

		if val is None and toggle is False:
			return

		if all:
			if toggle:
				pwd.toggle_all_marks()
			else:
				pwd.mark_all(val)
		else:
			item = self.env.cf
			if item is not None:
				if toggle:
					pwd.toggle_mark(item)
				else:
					pwd.mark_item(item, val)

		if movedown:
			self.move_pointer(relative=1)

		if hasattr(self.ui, 'redraw_main_column'):
			self.ui.redraw_main_column()
		if hasattr(self.ui, 'status'):
			self.ui.status.need_redraw = True

	# ------------------------------------ filesystem operations

	def copy(self):
		"""Copy the selected items"""

		selected = self.env.get_selection()
		self.env.copy = set(f for f in selected if f in self.env.pwd.files)
		self.env.cut = False
	
	def cut(self):
		self.copy()
		self.env.cut = True
	
	def paste_symlink(self):
		from os import symlink, getcwd
		from os.path import join

		copied_files = self.env.copy

		if not copied_files:
			return

		for f in copied_files:
			try:
				symlink(f.path, join(getcwd(), f.basename))
			except Exception as x:
				self.notify(x)

	def paste(self):
		"""Paste the selected items into the current directory"""
		from os.path import join, isdir
		from ranger.ext import shutil_generatorized as shutil_g
		from ranger.fsobject.loader import LoadableObject
		copied_files = tuple(self.env.copy)

		if not copied_files:
			return

		original_path = self.env.pwd.path
		try:
			one_file = copied_files[0]
		except:
			one_file = None

		if self.env.cut:
			self.env.copy.clear()
			self.env.cut = False
			if len(copied_files) == 1:
				descr = "moving: " + one_file.path
			else:
				descr = "moving files from: " + one_file.dirname
			def generate():
				for f in copied_files:
					for _ in shutil_g.move(f.path, original_path):
						yield
				pwd = self.env.get_directory(original_path)
				pwd.load_content()
		else:
			if len(copied_files) == 1:
				descr = "copying: " + one_file.path
			else:
				descr = "copying files from: " + one_file.dirname
			def generate():
				for f in self.env.copy:
					if isdir(f.path):
						for _ in shutil_g.copytree(f.path,
								join(self.env.pwd.path, f.basename)):
							yield
					else:
						for _ in shutil_g.copy2(f.path, original_path):
							yield
				pwd = self.env.get_directory(original_path)
				pwd.load_content()

		self.loader.add(LoadableObject(generate(), descr))

	def delete(self):
		self.notify("Deleting!", duration=1)
		selected = self.env.get_selection()
		self.env.copy -= selected
		if selected:
			for f in selected:
				if os.path.isdir(f.path) and not os.path.islink(f.path):
					try:
						shutil.rmtree(f.path)
					except OSError as err:
						self.notify(str(err), bad=True)
				else:
					try:
						os.remove(f.path)
					except OSError as err:
						self.notify(str(err), bad=True)
	
	def mkdir(self, name):
		try:
			os.mkdir(os.path.join(self.env.pwd.path, name))
		except OSError as err:
			self.notify(str(err), bad=True)

	
	def rename(self, src, dest):
		if hasattr(src, 'path'):
			src = src.path

		try:
			os.rename(src, dest)
		except OSError as err:
			self.notify(str(err), bad=True)
