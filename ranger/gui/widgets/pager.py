"""
The pager displays text and allows you to scroll inside it.
"""
from ranger import log
from . import Widget
from ranger.container.commandlist import CommandList
from ranger.ext.move import move_between

class Pager(Widget):
	source = None
	source_is_stream = False
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
	
	def close(self):
		if self.source and self.source_is_stream:
			self.source.close()
	
	def draw(self):
		line_gen = self._generate_lines(
				starty=self.scroll_begin, startx=self.startx)

		for line, i in zip(line_gen, range(self.hei)):
			y, x = self.y + i, self.x

			try:
				self.win.addstr(y, x, line)
			except:
				pass
	
	def move(self, relative=0, absolute=None):
		i = self.scroll_begin
		if isinstance(absolute, int):
			i = absolute

		if isinstance(relative, int):
			i += relative

		length = len(self.lines) - self.hei - 1
		log('before: ' + str(length))

		if i >= length:
			self._get_line(i+self.hei)

		length = len(self.lines) - self.hei - 1
		log('after: ' + str(length))

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
	
	def set_source(self, source):
		if self.source and self.source_is_stream:
			self.source.close()

		if hasattr(source, '__getitem__'):
			self.source_is_stream = False
			self.lines = source
		elif hasattr(source, 'readline'):
			self.source_is_stream = True
			self.lines = []
		else:
			self.source = None
			self.source_is_stream = False
			return False

		self.source = source
		return True

	def _get_line(self, n, attempt_to_read=True):
		try:
			return self.lines[n]
		except (KeyError, IndexError):
			if attempt_to_read and self.source_is_stream:
				for l in self.source:
					self.lines.append(l)
					if len(self.lines) > n:
						break
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
