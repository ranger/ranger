import ranger.widget
from ranger.debug import log
import curses

class WDisplay(ranger.widget.Widget):
	def __init__(self, win, level):
		ranger.widget.Widget.__init__(self,win)
		self.level = level
		self.main_display = False
		self.display_infostring = False
		self.scroll_begin = 0

	def feed_env(self, env):
		self.target = env.at_level(self.level)
		self.show_hidden = env.opt['show_hidden']
		self.scroll_offset = env.opt['scroll_offset']

	def draw(self):
		from ranger.file import File
		from ranger.directory import Directory

		if self.target is None:
			pass
		elif type(self.target) == File:
			self.draw_file()
		elif type(self.target) == Directory:
			self.draw_directory()
		else:
			self.win.addnstr(self.y, self.x, "unknown type.", self.wid)

	def draw_file(self):
		if not self.target.accessible:
			self.win.addnstr(self.y, self.x, "not accessible", self.wid)
			return
		self.win.addnstr(self.y, self.x, "this is a file.", self.wid)

	def draw_directory(self):
		self.target.show_hidden = self.show_hidden
		self.target.load_content_if_outdated()
		main_display = self.main_display

		if not self.target.accessible:
			self.win.addnstr(self.y, self.x, "not accessible", self.wid)
			return

		self.set_scroll_begin()

		for line in range(self.hei):
			i = line + self.scroll_begin
			# last file reached?
			try: drawed = self.target[i]
			except IndexError: break

			invert = i == self.target.pointed_index
			if invert:
				self.win.attrset(curses.A_REVERSE)

			if self.main_display:
				self.win.addnstr(
						self.y + line,
						self.x + 1,
						' ' + drawed.basename + ' ',
						self.wid - 2)
			else:
				self.win.addnstr(
						self.y + line,
						self.x,
						drawed.basename,
						self.wid)

			if self.display_infostring and drawed.infostring:
				info = drawed.infostring
				x = self.x + self.wid - 1 - len(info)
				if x > self.x:
					self.win.addstr(self.y + line, x, str(info) + ' ')
			if invert:
				self.win.attrset(curses.A_NORMAL)

	def get_scroll_begin(self):
		offset = self.scroll_offset
		dirsize = len(self.target)
		winsize = self.hei
		halfwinsize = winsize // 2
		index = self.target.pointed_index or 0
		original = self.target.scroll_begin
		projected = index - original

		upper_limit = winsize - 1 - offset
		lower_limit = offset

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
		self.scroll_begin = self.get_scroll_begin()
		self.target.scroll_begin = self.scroll_begin

