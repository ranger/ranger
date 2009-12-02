from ranger.gui.widget import Widget as SuperClass

class WDisplay(SuperClass):
	def __init__(self, win, colorscheme, level):
		SuperClass.__init__(self, win, colorscheme)
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
		
	def click(self, event, fm):
		from ranger.fsobject import T_DIRECTORY

		if self.target is None:
			pass

		elif self.target.type is T_DIRECTORY:
			index = self.scroll_begin + event.y - self.y

			if event.pressed(1):
				if not self.main_display:
					fm.enter_dir(self.target.path)

				if index < len(self.target):
					fm.move_pointer(absolute = index)
			elif event.pressed(3):
				try:
					clicked_file = self.target[index]
					fm.enter_dir(clicked_file.path)
				except:
					pass

		else:
			if self.level > 0:
				fm.move_right()

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

	def draw_directory(self):
		from ranger.directory import Directory
		import curses
		import stat

		self.target.show_hidden = self.show_hidden
		self.target.load_content_if_outdated()
		self.target.directories_first = self.directories_first
		self.target.sort_if_outdated()

		base_color = ['in_display']

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

		selected_i = self.target.pointed_index
		for line in range(self.hei):
			i = line + self.scroll_begin

			try:
				drawed = self.target[i]
			except IndexError:
				break

			this_color = base_color[:]

			if i == selected_i:
				this_color.append('selected')

			if isinstance(drawed, Directory):
				this_color.append('directory')
			else:
				this_color.append('file')

			if drawed.stat is not None and drawed.stat.st_mode & stat.S_IXUSR:
				this_color.append('executable')

			if drawed.islink:
				this_color.append('link')

			string = drawed.basename
			if self.main_display:
				self.win.addnstr(self.y + line, self.x+1, drawed.basename, self.wid-2)
			else:
				self.win.addnstr(self.y + line, self.x, drawed.basename, self.wid)

			if self.display_infostring and drawed.infostring:
				info = drawed.infostring
				x = self.x + self.wid - 1 - len(info)
				if x > self.x:
					self.win.addstr(self.y + line, x, str(info) + ' ')

			self.color_at(self.y + line, self.x, self.wid, this_color)

			self.color_reset()

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
		self.scroll_begin = self.get_scroll_begin()
		self.target.scroll_begin = self.scroll_begin

	# TODO: does not work if options.scroll_offset is high,
	# relative > 1 and you scroll from scroll_begin = 1 to 0
	def scroll(self, relative):
		self.set_scroll_begin()
		old_value = self.target.scroll_begin
		self.target.scroll_begin += relative
		self.set_scroll_begin()

		if self.target.scroll_begin == old_value:
			self.target.move_pointer(relative = relative)
			self.target.scroll_begin += relative


