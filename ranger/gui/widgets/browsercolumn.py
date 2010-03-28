# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""The BrowserColumn widget displays the contents of a directory or file."""
import re
from time import time

from . import Widget
from .pager import Pager

# Don't even try to preview files which mach this regular expression:
PREVIEW_BLACKLIST = re.compile(r"""
		# look at the extension:
		\.(
			# one character extensions:
				[oa]
			# media formats:
				| avi | [mj]pe?g | mp\d | og[gmv] | wm[av] | mkv | flv
				| png | bmp | vob | wav | mpc | flac | divx? | xcf | pdf
			# binary files:
				| torrent | class | so | img | py[co] | dmg
			# containers:
				| iso | rar | zip | 7z | tar | gz | bz2 | tgz
		)
		# ignore filetype-independent suffixes:
			(\.part|\.bak|~)?
		# ignore fully numerical file extensions:
			(\.\d+)*?
		$
""", re.VERBOSE | re.IGNORECASE)

PREVIEW_WHITELIST = re.compile(r"""
		\.(
			txt | py | c
		)
		# ignore filetype-independent suffixes:
			(\.part|\.bak|~)?
		$
""", re.VERBOSE | re.IGNORECASE)

class BrowserColumn(Pager):
	main_column = False
	display_infostring = False
	scroll_begin = 0
	target = None
	tagged_marker = '*'
	last_redraw_time = -1

	old_dir = None
	old_cf = None

	def __init__(self, win, level):
		"""
		win = the curses window object of the BrowserView
		level = what to display?

		level >0 => previews
		level 0 => current file/directory
		level <0 => parent directories
		"""
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
				if not self.main_column:
					self.fm.enter_dir(self.target.path)

				if index < len(self.target):
					self.fm.move_pointer(absolute = index)
			elif event.pressed(3):
				try:
					clicked_file = self.target.files[index]
					self.fm.enter_dir(clicked_file.path)
				except:
					pass

		else:
			if self.level > 0:
				self.fm.move_right()

		return True

	def has_preview(self):
		if self.target is None:
			return False

		if self.target.is_file:
			if not self._preview_this_file(self.target):
				return False

		if self.target.is_directory:
			if self.level > 0 and not self.settings.preview_directories:
				return False

		return True

	def poke(self):
		Widget.poke(self)
		self.target = self.env.at_level(self.level)

	def draw(self):
		"""Call either _draw_file() or _draw_directory()"""
		if self.target != self.old_dir:
			self.need_redraw = True
			self.old_dir = self.target

		if self.target and self.target.is_directory \
				and (self.level <= 0 or self.settings.preview_directories):
			if self.target.pointed_obj != self.old_cf:
				self.need_redraw = True
				self.old_cf = self.target.pointed_obj

			if self.target.load_content_if_outdated() \
			or self.target.sort_if_outdated() \
			or self.last_redraw_time < self.target.last_update_time:
				self.need_redraw = True

		if self.need_redraw:
			self.win.erase()
			if self.target is None:
				pass
			elif self.target.is_file:
				Pager.open(self)
				self._draw_file()
			elif self.target.is_directory:
				self._draw_directory()
				Widget.draw(self)
			self.need_redraw = False
			self.last_redraw_time = time()

	def _preview_this_file(self, target):
		if not self.settings.preview_files:
			return False
		if not self.target or not self.target.is_file:
			return False
		maxsize = self.settings.max_filesize_for_preview
		if maxsize is not None and target.size > maxsize:
			return False
		if PREVIEW_WHITELIST.search(target.basename):
			return True
		if PREVIEW_BLACKLIST.search(target.basename):
			return False
		if target.is_binary():
			return False
		return True

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
		import stat

		if self.level > 0 and not self.settings.preview_directories:
			return

		base_color = ['in_browser']

		self.target.use()

		self.win.move(0, 0)

		if not self.target.content_loaded:
			self.color(base_color)
			self.win.addnstr("...", self.wid)
			self.color_reset()
			return

		if self.main_column:
			base_color.append('main_column')

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
				drawed = self.target.files[i]
			except IndexError:
				break

			this_color = base_color + list(drawed.mimetype_tuple)
			text = drawed.basename
			tagged = self.fm.tags and drawed.realpath in self.fm.tags

			if i == selected_i:
				this_color.append('selected')

			if drawed.marked:
				this_color.append('marked')
				if self.main_column:
					text = " " + text

			if tagged:
				this_color.append('tagged')
				if self.main_column:
					text = self.tagged_marker + text

			if drawed.is_directory:
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
				if self.main_column:
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

			if self.main_column and tagged and self.wid > 2:
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
		self.need_redraw = True
		self._set_scroll_begin()
		old_value = self.target.scroll_begin
		self.target.scroll_begin += relative
		self._set_scroll_begin()

		if self.target.scroll_begin == old_value:
			self.target.move(relative = relative)
			self.target.scroll_begin += relative

	def __str__(self):
		return self.__class__.__name__ + ' at level ' + str(self.level)
