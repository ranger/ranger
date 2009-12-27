"""The FileList widget displays the contents of a directory or file."""
from . import Widget
from ..displayable import DisplayableContainer
from .pager import Pager

class FileList(Widget, DisplayableContainer):
	main_display = False
	display_infostring = False
	scroll_begin = 0
	target = None
	postpone_drawing = False
	tagged_marker = '*'

	def __init__(self, win, level):
		DisplayableContainer.__init__(self, win)
		self.pager = Pager(win)
		self.add_obj(self.pager)
		self.level = level
	
	def resize(self, *args):
		DisplayableContainer.resize(self, *args)
		self.pager.resize(*args)

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
		"""Call either draw_file() or draw_directory()"""
		from ranger.fsobject.file import File
		from ranger.fsobject.directory import Directory

		self.pager.visible = False
		if self.target is None:
			pass
		elif type(self.target) == File:
			self.draw_file()
		elif type(self.target) == Directory:
			self.draw_directory()

		DisplayableContainer.draw(self)

	def finalize(self):
		if self.postpone_drawing:
			self.target.load_content_if_outdated()
			self.draw_directory()
			self.postpone_drawing = False

	def _preview_this_file(self, target):
		return target.document and not self.settings.preview_files

	def draw_file(self):
		"""Draw a preview of the file, if the settings allow it"""
		if not self.target.accessible:
			self.win.addnstr(self.y, self.x, "not accessible", self.wid)
			return

		if not self._preview_this_file(self.target):
			return
		
		try:
			f = open(self.target.path, 'r')
		except:
			pass
		else:
			self.pager.visible = True
			self.pager.set_source(f)

	def draw_directory(self):
		"""Draw the contents of a directory"""
		from ranger.fsobject.directory import Directory
		import stat

		base_color = ['in_display']

		self.target.use()

		if not self.target.content_loaded:
#			if self.target.force_load:
#				self.target.stopped = False
#
#			else:
#				if not self.target.stopped:
#					
#					if maxdirsize is not None and self.target.accessible \
#							and self.target.size > maxdirsize:
#						self.target.stopped = True
#
			maxdirsize = self.settings.max_dirsize_for_autopreview
			if not self.target.force_load and maxdirsize is not None \
					and self.target.accessible \
					and self.target.size > maxdirsize:
				self.color(base_color, 'error')
				self.win.addnstr(self.y, self.x, "no preview", self.wid)
				self.color_reset()
				return

			if self.settings.auto_load_preview:
				self.color(base_color)
				self.win.addnstr(self.y, self.x, "...", self.wid)
				self.postpone_drawing = True
				self.color_reset()
				return
			else:
				self.color(base_color, 'error')
				self.win.addnstr(self.y, self.x, "not loaded", self.wid)
				self.color_reset()
				return

		if not self.target.load_content_if_outdated():
			self.target.sort_if_outdated()

		if self.main_display:
			base_color.append('maindisplay')

		if not self.target.accessible:
			self.color(base_color, 'error')
			self.win.addnstr(self.y, self.x, "not accessible", self.wid)
			self.color_reset()
			return

		if self.target.empty():
			self.color(base_color, 'empty')
			self.win.addnstr(self.y, self.x, "empty", self.wid)
			self.color_reset()
			return

		self.set_scroll_begin()

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
			if self.main_display:
				if tagged:
					if self.wid > 1:
						self.win.addnstr(self.y + line, self.x,
								text, self.wid - 2)
				elif self.wid > 2:
					self.win.addnstr(self.y + line, self.x + 1,
							text, self.wid - 2)
			else:
				self.win.addnstr(self.y + line, self.x, text, self.wid)

			if self.display_infostring and drawed.infostring:
				info = drawed.infostring
				x = self.x + self.wid - 1 - len(info)
				if x > self.x:
					self.win.addstr(self.y + line, x, str(info) + ' ')

			self.color_at(self.y + line, self.x, self.wid, this_color)

			if self.main_display and tagged and self.wid > 2:
				this_color.append('tag_marker')
				self.color_at(self.y + line, self.x,
						len(self.tagged_marker), this_color)

			self.color_reset()

	def get_scroll_begin(self):
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
			return self.get_scroll_begin()

		if projected < upper_limit and projected > lower_limit:
			return original

		if projected > upper_limit:
			return min( dirsize - winsize,
					original + (projected - upper_limit))

		if projected < upper_limit:
			return max( 0,
					original - (lower_limit - projected))
		
		return original

	def set_scroll_begin(self):
		"""Updates the scroll_begin value"""
		self.scroll_begin = self.get_scroll_begin()
		self.target.scroll_begin = self.scroll_begin

	# TODO: does not work if options.scroll_offset is high,
	# relative > 1 and you scroll from scroll_begin = 1 to 0
	def scroll(self, relative):
		"""scroll by n lines"""
		self.set_scroll_begin()
		old_value = self.target.scroll_begin
		self.target.scroll_begin += relative
		self.set_scroll_begin()

		if self.target.scroll_begin == old_value:
			self.target.move(relative = relative)
			self.target.scroll_begin += relative
