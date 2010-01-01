from ranger.shared import SettingsAware
import _curses

class CursesShortcuts(SettingsAware):

	"""
	This class defines shortcuts to faciliate operations with curses.
	color(*keys) -- sets the color associated with the keys from
		the current colorscheme.
	color_at(y, x, wid, *keys) -- sets the color at the given position
	color_reset() -- resets the color to the default
	addstr(*args) -- failsafe version of self.win.addstr(*args)
	"""

	def addstr(self, *args):
		try:
			self.win.addstr(*args)
		except _curses.error:
			pass

	def addnstr(self, *args):
		try:
			self.win.addnstr(*args)
		except _curses.error:
			pass

	def color(self, keylist = None, *keys):
		"""Change the colors from now on."""
		keys = combine(keylist, keys)
		attr = self.settings.colorscheme.get_attr(*keys)
		try:
			self.win.attrset(attr)
		except _curses.error:
			pass

	def color_at(self, y, x, wid, keylist = None, *keys):
		"""Change the colors at the specified position"""
		keys = combine(keylist, keys)
		attr = self.settings.colorscheme.get_attr(*keys)
		try:
			self.win.chgat(y, x, wid, attr)
		except _curses.error:
			pass
	
	def color_reset(self):
		"""Change the colors to the default colors"""
		CursesShortcuts.color(self, 'reset')

def combine(seq, tup):
	"""Add seq and tup. Ensures that the result is a tuple."""
	try:
		if isinstance(seq, str): raise TypeError
		return tuple(tuple(seq) + tup)
	except TypeError:
		try:
			return tuple((seq, ) + tup)
		except:
			return ()
