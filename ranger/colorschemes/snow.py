from ranger.gui.colorscheme import ColorScheme
from ranger.gui.color import *

class Snow(ColorScheme):
	def use(self, context):
		fg, bg, attr = default_colors

		if context.reset:
			pass

		elif context.in_browser:
			if context.selected:
				attr = reverse
			else:
				attr = normal

			if context.directory:
				attr |= bold

		if context.highlight:
			attr |= reverse

		return fg, bg, attr
