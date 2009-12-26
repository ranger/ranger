import os
import shutil

from ranger.shared import EnvironmentAware, SettingsAware
from ranger import fsobject

class Actions(EnvironmentAware, SettingsAware):
	def search_forward(self):
		"""Search forward for the regexp in self.env.last_search"""
		if self.env.pwd:
			self.env.pwd.search(self.env.last_search)

	def search_backward(self):
		"""Search backward for the regexp in self.env.last_search"""
		if self.env.pwd:
			self.env.pwd.search(self.env.last_search, -1)

	def interrupt(self):
		"""
		Waits a short time.
		If CTRL+C is pressed while waiting, the program will be exited.
		"""
		import time
		self.env.key_clear()
		try:
			time.sleep(0.2)
		except KeyboardInterrupt:
			raise SystemExit()

	def resize(self):
		"""Update the size of the UI"""
		self.ui.update_size()

	def exit(self):
		"""Exit the program"""
		raise SystemExit()

	def enter_dir(self, path):
		"""Enter the directory at the given path"""
		return self.env.enter_dir(path)

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

	def enter_bookmark(self, key):
		"""Enter the bookmark with the name <key>"""
		from ranger.container.bookmarks import NonexistantBookmark
		try:
			destination = self.bookmarks[key]
			pwd = self.env.pwd
			if destination.path != pwd.path:
				self.bookmarks.enter(key)
				self.bookmarks.remember(pwd)
		except NonexistantBookmark:
			pass

	def set_bookmark(self, key):
		"""Set the bookmark with the name <key> to the current directory"""
		self.bookmarks[key] = self.env.pwd

	def unset_bookmark(self, key):
		"""Delete the bookmark with the name <key>"""
		self.bookmarks.delete(key)

	def move_left(self, n=1):
		"""Enter the parent directory"""
		try:
			directory = os.path.join(*(['..'] * n))
		except:
			return
		self.env.enter_dir(directory)
	
	def move_right(self, mode=0):
		"""Enter the current directory or execute the current file"""
		cf = self.env.cf
		marked_items = self.env.pwd.marked_items
		sel = self.env.get_selection()

		if not self.env.enter_dir(cf):
			if sel:
				if not self.execute_file(sel, mode=mode):
					self.open_console('@')

	def history_go(self, relative):
		"""Move back and forth in the history"""
		self.env.history_go(relative)
	
	def handle_mouse(self):
		"""Handle mouse-buttons if one was pressed"""
		self.ui.handle_mouse()

	def execute_file(self, files, app='', flags='', mode=0):
		"""Execute a file.
		app is the name of a method in Applications, without the "app_"
		flags is a string consisting of applications.ALLOWED_FLAGS
		mode is a positive integer.
		Both flags and mode specify how the program is run."""

		if isinstance(files, set):
			files = list(files)
		elif type(files) not in (list, tuple):
			files = [files]

		return self.apps.get(app)(
				mainfile = files[0],
				files = list(files),
				flags = flags,
				mode = mode,
				fm = self,
				stdin = None,
				apps = self.apps)
	
	def edit_file(self):
		"""Calls execute_file with the current file and app='editor'"""
		if self.env.cf is None:
			return
		self.execute_file(self.env.cf, app = 'editor')

	def open_console(self, mode=':', string=''):
		"""Open the console if the current UI supports that"""
		if hasattr(self.ui, 'open_console'):
			self.ui.open_console(mode, string)

	def move_pointer(self, relative = 0, absolute = None):
		"""Move the pointer down by <relative> or to <absolute>"""
		self.env.pwd.move(relative, absolute)

	def move_pointer_by_pages(self, relative):
		"""Move the pointer down by <relative> pages"""
		self.env.pwd.move(relative=int(relative * self.env.termsize[0]))

	def move_pointer_by_percentage(self, relative=0, absolute=None):
		"""Move the pointer down by <relative>% or to <absolute>%"""
		try:
			factor = len(self.env.pwd) / 100.0
		except:
			return
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
	
	def spawn(self, command):
		from ranger.applications import spawn
		spawn(command, fm=self)
	
	def force_load_preview(self):
		cf = self.env.cf
		if cf is not None:
			cf.force_load = True

# ------------------------------------ filesystem operations

	def copy(self):
		"""Copy the selected items"""

		selected = self.env.get_selection()
		self.env.copy = set(f for f in selected if f in self.env.pwd.files)
		self.env.cut = False
	
	def cut(self):
		self.copy()
		self.env.cut = True

	def paste(self):
		"""Paste the selected items into the current directory"""
		from os.path import join, isdir
		from ranger.ext import shutil_generatorized as shutil_g
		from ranger.fsobject.loader import LoadableObject
		copied_files = tuple(self.env.copy)

		if not copied_files:
			return

		pwd = self.env.pwd
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
					for _ in shutil_g.move(f.path, pwd.path):
						yield
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
						for _ in shutil_g.copy2(f.path, self.env.pwd.path):
							yield
				pwd.load_content()

		self.loader.add(LoadableObject(generate(), descr))

	def delete(self):
		msg = self.notify("Deleting ...", duration=0)
		selected = self.env.get_selection()
		self.env.copy -= selected
		if selected:
			for f in selected:
				if os.path.isdir(f.path):
					try:
						shutil.rmtree(f.path)
					except OSError as err:
						self.notify(str(err), bad=True)
				else:
					try:
						os.remove(f.path)
					except OSError as err:
						self.notify(str(err), bad=True)
		msg.delete()
	
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

	
	def notify(self, text, duration=4, bad=False):
		try:
			method = self.ui.display
		except AttributeError:
			pass
		else:
			return method(text, duration=duration, bad=bad)
	
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

	# aliases:
	cd = enter_dir
