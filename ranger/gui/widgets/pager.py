# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
# Copyright (C) 2010 David Barnett <davidbarnett2@gmail.com>
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

"""
The pager displays text and allows you to scroll inside it.
"""
from . import Widget
from ranger.gui import ansi
from ranger.ext.direction import Direction

# TODO: Scrolling in embedded pager
class Pager(Widget):
	source = None
	source_is_stream = False

	old_source = None
	old_scroll_begin = 0
	old_startx = 0
	max_width = None
	def __init__(self, win, embedded=False):
		Widget.__init__(self, win)
		self.embedded = embedded
		self.scroll_begin = 0
		self.startx = 0
		self.markup = None
		self.lines = []

	def open(self):
		self.scroll_begin = 0
		self.markup = None
		self.max_width = 0
		self.startx = 0
		self.need_redraw = True

	def close(self):
		if self.source and self.source_is_stream:
			self.source.close()

	def finalize(self):
		self.fm.ui.win.move(self.y, self.x)

	def draw(self):
		if self.old_source != self.source:
			self.old_source = self.source
			self.need_redraw = True

		if self.old_scroll_begin != self.scroll_begin or \
				self.old_startx != self.startx:
			self.old_startx = self.startx
			self.old_scroll_begin = self.scroll_begin
		self.need_redraw = True

		if self.need_redraw:
			self.win.erase()
			line_gen = self._generate_lines(
					starty=self.scroll_begin, startx=self.startx)

			for line, i in zip(line_gen, range(self.hei)):
				self._draw_line(i, line)
			self.need_redraw = False

	def _draw_line(self, i, line):
		if self.markup is None:
			self.addstr(i, 0, line)
		elif self.markup == 'ansi':
			try:
				self.win.move(i, 0)
			except:
				pass
			else:
				for chunk in ansi.text_with_fg_bg_attr(line):
					if isinstance(chunk, tuple):
						self.set_fg_bg_attr(*chunk)
					else:
						self.addstr(chunk)

	def move(self, narg=None, **kw):
		direction = Direction(kw)
		if direction.horizontal():
			self.startx = direction.move(
					direction=direction.right(),
					override=narg,
					maximum=self.max_width,
					current=self.startx,
					pagesize=self.wid,
					offset=-self.wid + 1)
		if direction.vertical():
			if self.source_is_stream:
				self._get_line(self.scroll_begin + self.hei * 2)
			self.scroll_begin = direction.move(
					direction=direction.down(),
					override=narg,
					maximum=len(self.lines),
					current=self.scroll_begin,
					pagesize=self.hei,
					offset=-self.hei + 1)

	def press(self, key):
		self.env.keymaps.use_keymap('pager')
		self.fm.ui.press(key)

	def set_source(self, source, strip=False):
		if self.source and self.source_is_stream:
			self.source.close()

		self.max_width = 0
		if isinstance(source, str):
			self.source_is_stream = False
			self.lines = source.splitlines()
			if self.lines:
				self.max_width = max(len(line) for line in self.lines)
		elif hasattr(source, '__getitem__'):
			self.source_is_stream = False
			self.lines = source
			if self.lines:
				self.max_width = max(len(line) for line in source)
		elif hasattr(source, 'readline'):
			self.source_is_stream = True
			self.lines = []
		else:
			self.source = None
			self.source_is_stream = False
			return False
		self.markup = 'ansi'

		if not self.source_is_stream and strip:
			self.lines = map(lambda x: x.strip(), self.lines)

		self.source = source
		return True

	def click(self, event):
		n = event.ctrl() and 1 or 3
		direction = event.mouse_wheel_direction()
		if direction:
			self.move(down=direction * n)
		return True

	def _get_line(self, n, attempt_to_read=True):
		assert isinstance(n, int), n
		try:
			return self.lines[n]
		except (KeyError, IndexError):
			if attempt_to_read and self.source_is_stream:
				try:
					for l in self.source:
						if len(l) > self.max_width:
							self.max_width = len(l)
						self.lines.append(l)
						if len(self.lines) > n:
							break
				except (UnicodeError, IOError):
					pass
				return self._get_line(n, attempt_to_read=False)
			return ""

	def _generate_lines(self, starty, startx):
		i = starty
		if not self.source:
			raise StopIteration
		while True:
			try:
				line = self._get_line(i).expandtabs(4)
				if self.markup is 'ansi':
					line = ansi.char_slice(line, startx, self.wid) + ansi.reset
				else:
					line = line[startx:self.wid + startx]
				yield line.rstrip()
			except IndexError:
				raise StopIteration
			i += 1
