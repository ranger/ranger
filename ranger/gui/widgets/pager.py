"""
The pager displays text and allows you to scroll inside it.
"""
from ranger import log
from . import Widget

class Pager(Widget):
	source = None
	source_is_stream = False
	def __init__(self, win):
		Widget.__init__(self, win)
		self.scroll_begin = 0

#		self.commandlist = CommandList()
#		self.settings.keys.initialize_pager_commands( \
#				self.commandlist)
	
	def draw(self):
		line_gen = self._generate_lines(
				starty=self.scroll_begin, startx=0)

		for line, i in zip(line_gen, range(self.hei)):
			y, x = self.y + i, self.x

			try:
				self.win.addstr(y, x, line)
			except:
				pass
	
	def set_source(self, source):
		if self.source and self.source_is_stream:
			self.source.close()

		if hasattr(source, '__getitem__'):
			self.source_is_stream = True
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
