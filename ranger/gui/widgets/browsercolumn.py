"""The BrowserColumn widget displays the contents of a directory or file."""
from . import Widget
from .pager import Pager
from ranger import log

class BrowserColumn(Pager, Widget):
	main_display = False
	display_infostring = False
	scroll_begin = 0
	target = None
	postpone_drawing = False
	tagged_marker = '*'

	def __init__(self, win, level):
		Pager.__init__(self, win)
		Widget.__init__(self, win)
		self.level = level
	
	def resize(self, y, x, hei, wid):
		Widget.resize(self, y, x, hei, wid)

	def click(self, event):
		"""Handle a MouseEvent"""
		from ranger.fsobject.fsobject import T_DIRECTORY

		if not (event.pressed(1) or event.pressed(3)):
			return False

		if self.target is None:
			pass

		elif self.target.type is T_DIRECTORY:
			index = self.scroll_begin + event.y - self.y

			if event.pressed(1):
				if not self.main_display:
					self.fm.enter_dir(self.target.path)

				if index < len(self.target):
					self.fm.move_pointer(absolute = index)
			elif event.pressed(3):
				try:
					clicked_file = self.target[index]
					self.fm.enter_dir(clicked_file.path)
				except:
					pass

		else:
			if self.level > 0:
				self.fm.move_right()

		return True

	def has_preview(self):
		from ranger.fsobject.file import File
		from ranger.fsobject.directory import Directory

		if self.target is None:
			return False

		if isinstance(self.target, File):
			if not self._preview_this_file(self.target):
				return False

		return True

	def poke(self):
		self.target = self.env.at_level(self.level)

	def draw(self):
		"""Call either _draw_file() or _draw_directory()"""
		from ranger.fsobject.file import File
		from ranger.fsobject.directory import Directory

#		self.pager.visible = False
		if self.target is None:
			pass
		elif type(self.target) == File:
			Pager.open(self)
			self._draw_file()
		elif type(self.target) == Directory:
			self._draw_directory()
			Widget.draw(self)

	def _preview_this_file(self, target):
		return target.document and not self.settings.preview_files

	def _draw_file(self):
		"""Draw a preview of the file, if the settings allow it"""
		self.win.move(0, 0)
		if not self.target.accessible:
			self.win.addnstr("not accessible", self.wid)
			Pager.close(self)
			return

		if not self._preview_this_file(self.target):
			Pager.close(self)
			return
		
		try:
			f = open(self.target.path, 'r')
		except:
			Pager.close(self)
		else:
			self.set_source(f)
			Pager.draw(self)

	def _draw_directory(self):
		"""Draw the contents of a directory"""
		from ranger.fsobject.directory import Directory
		import stat

		base_color = ['in_display']

		self.target.use()

		self.win.move(0, 0)

		if not self.target.load_content_if_outdated():
			self.target.sort_if_outdated()

		if not self.target.content_loaded:
			maxdirsize = self.settings.max_dirsize_for_autopreview
			if not self.target.force_load and maxdirsize is not None \
					and self.target.accessible \
					and self.target.size > maxdirsize:
				self.color(base_color, 'error')
				self.win.addnstr("no preview", self.wid)
				self.color_reset()
				return

			if self.settings.auto_load_preview:
				self.color(base_color)
				self.win.addnstr("...", self.wid)
				self.postpone_drawing = True
				self.color_reset()
				return
			else:
				self.color(base_color, 'error')
				self.win.addnstr("not loaded", self.wid)
				self.color_reset()
				return

		if self.main_display:
			base_color.append('maindisplay')

		if not self.target.accessible:
			self.color(base_color, 'error')
			self.win.addnstr("not accessible", self.wid)
			self.color_reset()
			return

		if self.target.empty():
			self.color(base_color, 'empty')
			self.win.addnstr("empty", self.wid)
			self.color_reset()
			return

		self._set_scroll_begin()

		selected_i = self.target.pointer
		for line in range(self.hei):
			i = line + self.scroll_begin

			try:
				drawed = self.target[i]
			except IndexError:
				break

			this_color = base_color + list(drawed.mimetype_tuple)
			text = drawed.basename
			tagged = drawed.realpath in self.fm.tags

			if i == selected_i:
				this_color.append('selected')

			if drawed.marked:
				this_color.append('marked')

			if tagged:
				this_color.append('tagged')
				if self.main_display:
					text = self.tagged_marker + text

			if isinstance(drawed, Directory):
				this_color.append('directory')
			else:
				this_color.append('file')

			if drawed.stat is not None and drawed.stat.st_mode & stat.S_IXUSR:
				this_color.append('executable')

			if drawed.islink:
				this_color.append('link')
				this_color.append(drawed.exists and 'good' or 'bad')

			string = drawed.basename
			try:
				if self.main_display:
					if tagged:
						self.win.addnstr(line, 0, text, self.wid - 2)
					elif self.wid > 1:
						self.win.addnstr(line, 1, text, self.wid - 2)
				else:
					self.win.addnstr(line, 0, text, self.wid)

				if self.display_infostring and drawed.infostring:
					info = drawed.infostring
					x = self.wid - 1 - len(info)
					if x > self.x:
						self.win.addstr(line, x, str(info) + ' ')
			except:
				# the drawing of the last string will cause an error
				# because ncurses tries to move out of the bounds
				pass

			self.color_at(line, 0, self.wid, this_color)

			if self.main_display and tagged and self.wid > 2:
				this_color.append('tag_marker')
				self.color_at(line, 0, len(self.tagged_marker), this_color)

			self.color_reset()

	def _get_scroll_begin(self):
		"""Determines scroll_begin (the position of the first displayed file)"""
		offset = self.settings.scroll_offset
		dirsize = len(self.target)
		winsize = self.hei
		halfwinsize = winsize // 2
		index = self.target.pointer or 0
		original = self.target.scroll_begin
		projected = index - original

		upper_limit = winsize - 1 - offset
		lower_limit = offset

		if original < 0:
			return 0

		if dirsize < winsize:
			return 0

		if halfwinsize < offset:
			return min( dirsize - winsize, max( 0, index - halfwinsize ))

		if original > dirsize - winsize:
			self.target.scroll_begin = dirsize - winsize
			return self._get_scroll_begin()

		if projected < upper_limit and projected > lower_limit:
			return original

		if projected > upper_limit:
			return min( dirsize - winsize,
					original + (projected - upper_limit))

		if projected < upper_limit:
			return max( 0,
					original - (lower_limit - projected))
		
		return original

	def _set_scroll_begin(self):
		"""Updates the scroll_begin value"""
		self.scroll_begin = self._get_scroll_begin()
		self.target.scroll_begin = self.scroll_begin

	# TODO: does not work if options.scroll_offset is high,
	# relative > 1 and you scroll from scroll_begin = 1 to 0
	def scroll(self, relative):
		"""scroll by n lines"""
		self._set_scroll_begin()
		old_value = self.target.scroll_begin
		self.target.scroll_begin += relative
		self._set_scroll_begin()

		if self.target.scroll_begin == old_value:
			self.target.move(relative = relative)
			self.target.scroll_begin += relative
