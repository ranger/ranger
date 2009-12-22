import os
import shutil

from ranger.shared import EnvironmentAware, SettingsAware
from ranger import fsobject

class Actions(EnvironmentAware, SettingsAware):
	def search_forward(self):
		"""Search forward for the regexp in self.env.last_search"""
		if self.env.pwd:
			if self.env.pwd.search(self.env.last_search):
				self.env.cf = self.env.pwd.pointed_file

	def search_backward(self):
		"""Search backward for the regexp in self.env.last_search"""
		if self.env.pwd:
			if self.env.pwd.search(self.env.last_search, -1):
				self.env.cf = self.env.pwd.pointed_file

	def interrupt(self):
		"""Waits a short time.
		If CTRL+C is pressed while waiting, the program will be exited"""
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

	def move_left(self):
		"""Enter the parent directory"""
		self.env.enter_dir('..')
	
	def move_right(self, mode = 0):
		"""Enter the current directory or execute the current file"""
		cf = self.env.cf
		if not self.env.enter_dir(cf):
			if cf is not None:
				if not self.execute_file(cf, mode = mode):
					self.open_console('@')

	def history_go(self, relative):
		"""Move back and forth in the history"""
		self.env.history_go(relative)
	
	def handle_mouse(self):
		"""Handle mouse-buttons if one was pressed"""
		self.ui.handle_mouse()

	def execute_file(self, files, app = '', flags = '', mode = 0):
		"""Execute a file.
		app is the name of a method in Applications, without the "app_"
		flags is a string consisting of applications.ALLOWED_FLAGS
		mode is a positive integer.
		Both flags and mode specify how the program is run."""

		if type(files) not in (list, tuple):
			files = [files]

		return self.apps.get(app)(
				mainfile = files[0],
				files = files,
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
		self.env.cf = self.env.pwd.move_pointer(relative, absolute)

	def move_pointer_by_pages(self, relative):
		"""Move the pointer down by <relative> pages"""
		self.env.cf = self.env.pwd.move_pointer(
				relative = int(relative * self.env.termsize[0]))

	def scroll(self, relative):
		"""Scroll down by <relative> lines"""
		if hasattr(self.ui, 'scroll'):
			self.ui.scroll(relative)
			self.env.cf = self.env.pwd.pointed_file

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
	
	def force_load_preview(self, obj=None):
		if not obj:
			obj = self.env.cf

		if isinstance(obj, fsobject.Directory):
			if not obj.force_load:
				obj.force_load = True
			else:
				obj.load_content()


# ------------------------------------ filesystem operations

	def copy(self):
		"""Copy the selected items"""

		selected = set([self.env.cf])
		self.env.copy = set(f for f in selected if f in self.env.pwd.files)
		self.env.cut = False
	
	def cut(self):
		self.copy()
		self.env.cut = True

	def paste(self):
		"""Paste the selected items into the current directory"""
		from os.path import join, isdir
		copied_files = self.env.copy

		if not copied_files:
			return

		if self.env.cut:
			msg = self.notify("Moving ...", duration=0)
			self.ui.redraw()
			for f in self.env.copy:
				try:
					shutil.move(f.path, self.env.pwd.path)
				except (shutil.Error, IOError) as x:
					self.notify(str(x), bad=True)
			self.env.copy.clear()
			self.env.cut = False
		else:
			msg = self.notify("Copying ...", duration=0)
			self.ui.redraw()
			for f in self.env.copy:
				if isdir(f.path):
					try:
						shutil.copytree(f.path, join(self.env.pwd.path, f.basename))
					except (shutil.Error, IOError) as x:
						self.notify(str(x), bad=True)
				else:
					try:
						shutil.copy(f.path, self.env.pwd.path)
					except (shutil.Error, IOError) as x:
						self.notify(str(x), bad=True)
		msg.delete()

		self.env.pwd.load_content()

	def delete(self):
		msg = self.notify("Deleting ...", duration=0)
		selected = set([self.env.cf])
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
	
	def notify(self, text, duration=4, bad=False):
		try:
			method = self.ui.display
		except AttributeError:
			pass
		else:
			return method(text, duration=duration, bad=bad)

	# aliases:
	cd = enter_dir
