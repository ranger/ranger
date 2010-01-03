"""
The pager displays text and allows you to scroll inside it.
"""
from . import Widget
from ranger.container.commandlist import CommandList
from ranger.ext.move import move_between

class Pager(Widget):
	source = None
	source_is_stream = False

	old_source = None
	old_scroll_begin = 0
	old_startx = 0
	def __init__(self, win, embedded=False):
		Widget.__init__(self, win)
		self.embedded = embedded
		self.scroll_begin = 0
		self.startx = 0
		self.lines = []

		self.commandlist = CommandList()

		if embedded:
			keyfnc = self.settings.keys.initialize_embedded_pager_commands
		else:
			keyfnc = self.settings.keys.initialize_pager_commands

		keyfnc(self.commandlist)
	
	def open(self):
		self.scroll_begin = 0
		self.startx = 0
		self.need_redraw = True
	
	def close(self):
		if self.source and self.source_is_stream:
			self.source.close()
	
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
				try:
					self.addstr(i, 0, line)
				except TypeError:
					pass
			self.need_redraw = False
	
	def move(self, relative=0, absolute=None, pages=None, narg=None):
		i = self.scroll_begin
		if isinstance(absolute, int):
			if isinstance(narg, int):
				absolute = narg
			if absolute < 0:
				i = absolute + len(self.lines)
			else:
				i = absolute

		if relative != 0:
			if isinstance(pages, int):
				relative *= pages * self.hei
			if isinstance(narg, int):
				relative *= narg
		i = int(i + relative)

		length = len(self.lines) - self.hei
		if i >= length:
			self._get_line(i+self.hei)

		length = len(self.lines) - self.hei
		if i >= length:
			i = length

		if i < 0:
			i = 0

		self.scroll_begin = i
	
	def move_horizontal(self, relative=0, absolute=None):
		self.startx = move_between(
				current=self.startx,
				minimum=0,
				maximum=999,
				relative=relative,
				absolute=absolute)

	def press(self, key):
		try:
			tup = self.env.keybuffer.tuple_without_numbers()
			if tup:
				cmd = self.commandlist[tup]
			else:
				return
				
		except KeyError:
			self.env.key_clear()
		else:
			if hasattr(cmd, 'execute'):
				cmd.execute_wrap(self)
				self.env.key_clear()
	
	def set_source(self, source, strip=False):
		if self.source and self.source_is_stream:
			self.source.close()

		if isinstance(source, str):
			self.source_is_stream = False
			self.lines = source.split('\n')
		elif hasattr(source, '__getitem__'):
			self.source_is_stream = False
			self.lines = source
		elif hasattr(source, 'readline'):
			self.source_is_stream = True
			self.lines = []
		else:
			self.source = None
			self.source_is_stream = False
			return False

		if not self.source_is_stream and strip:
			self.lines = map(lambda x: x.strip(), self.lines)

		self.source = source
		return True

	def click(self, event):
		n = event.ctrl() and 1 or 3
		if event.pressed(4):
			self.move(relative = -n)
		elif event.pressed(2) or event.key_invalid():
			self.move(relative = n)
		return True

	def _get_line(self, n, attempt_to_read=True):
		try:
			return self.lines[n]
		except (KeyError, IndexError):
			if attempt_to_read and self.source_is_stream:
				try:
					for l in self.source:
						self.lines.append(l)
						if len(self.lines) > n:
							break
				except UnicodeError:
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
				line = line[startx:self.wid - 1 + startx].rstrip()
				yield line
			except IndexError:
				raise StopIteration
			i += 1
