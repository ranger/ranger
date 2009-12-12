"""The TitleBar widget displays the current path and some other useful
information."""

from . import Widget

class TitleBar(Widget):
	def draw(self):
		import curses, socket, os
		self.win.move(self.y, self.x)

		self.color('in_titlebar', 'hostname')
		string = os.getenv('LOGNAME') + '@' + socket.gethostname()
		self.win.addnstr(string, self.wid)

		for path in self.env.pathway:
			currentx = self.win.getyx()[1]

			if path.islink:
				self.color('in_titlebar', 'link')
			else:
				self.color('in_titlebar', 'directory')

			self.win.addnstr(path.basename + '/', max(self.wid - currentx, 0))
		if self.env.cf is not None:
			currentx = self.win.getyx()[1]
			self.color('in_titlebar', 'file')
			self.win.addnstr(self.env.cf.basename, max(self.wid - currentx, 0))

		self.color('in_titlebar', 'keybuffer')

		kb = str(self.env.keybuffer)
		if self.wid + self.x - currentx > len(kb):
			self.win.addstr(
					self.y,
					self.x + self.wid - len(kb) - 2,
					kb)

		self.color_reset()
