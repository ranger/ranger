from ranger.gui.widget import Widget as SuperClass

class WTitleBar(SuperClass):
	def feed_env(self, env):
		self.pathway = env.pathway
		self.cf = env.cf
		self.keybuffer = env.keybuffer

	def draw(self):
		import curses, socket, os
		self.win.move(self.y, self.x)

		try:
			self.color('in_titlebar', 'hostname')
			string = os.getenv('LOGNAME') + '@' + socket.gethostname()
			self.win.addnstr(string, self.wid)
		except:
			raise
			pass

		for path in self.pathway:
			currentx = self.win.getyx()[1]

			if path.islink:
				self.color('in_titlebar', 'link')
			else:
				self.color('in_titlebar', 'directory')

			self.win.addnstr(path.basename + '/', max(self.wid - currentx, 0))
		if self.cf is not None:
			currentx = self.win.getyx()[1]
			self.color('in_titlebar', 'file')
			self.win.addnstr(self.cf.basename, max(self.wid - currentx, 0))

		self.color('in_titlebar', 'keybuffer')

		kb = str(self.keybuffer)
		if self.wid + self.x - currentx > len(kb):
			self.win.addstr(
					self.y,
					self.x + self.wid - len(kb) - 2,
					kb)

		self.color_reset()

