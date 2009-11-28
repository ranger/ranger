import ranger.widget
from ranger.debug import log
from ranger.color import color_pairs
import curses
from ranger.widget import Widget as SuperClass
#from ranger.color import color

class WDisplay(SuperClass):
	def __init__(self, win, level):
		SuperClass.__init__(self,win)
		self.level = level
		self.main_display = False
		self.display_infostring = False
		self.scroll_begin = 0

	def feed_env(self, env):
		self.target = env.at_level(self.level)
		self.show_hidden = env.opt['show_hidden']
		self.scroll_offset = env.opt['scroll_offset']
		self.directories_first = env.opt['directories_first']
		self.preview_files = env.opt['preview_files']

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
		
		if self.preview_files:
			try:
				if self.target.size < 1024 * 20:
					f = open(self.target.path, 'r')
					for line in range(self.hei):
						read = f.readline().expandtabs()
						self.win.addnstr(self.y + line, self.x, read, self.wid)
			except:
				pass

		else:
			self.win.addnstr(self.y, self.x, "this is a file.", self.wid)

	def draw_directory(self):
		from ranger.directory import Directory
		self.target.show_hidden = self.show_hidden
		self.target.load_content_if_outdated()
		self.target.directories_first = self.directories_first
		self.target.sort_if_outdated()
		main_display = self.main_display

		if self.target.empty():
			self.color(bg=1)
			self.win.addnstr(self.y, self.x, "empty", self.wid)
			self.color()
			return

		if not self.target.accessible:
			self.win.addnstr(self.y, self.x, "not accessible", self.wid)
			return

#		log(color_pairs)

		self.set_scroll_begin()

		selected_i = self.target.pointed_index
		for line in range(self.hei):
			i = line + self.scroll_begin
			# last file reached?
			try: drawed = self.target[i]
			except IndexError: break

			if isinstance(drawed, Directory):
				self.color(fg = 4)
			else:
				self.color()

			invert = i == selected_i
			if invert:
				self.win.attron(curses.A_REVERSE)

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
			self.win.attrset(0)

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

