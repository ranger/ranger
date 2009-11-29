from ranger.gui.colorscheme import ColorScheme
from ranger.gui.color import *

class MyColorScheme(ColorScheme):
	def use(self, context):
		fg, bg, attr = default_colors

		if context.reset:
			pass

		elif context.in_display:
			if context.selected:
				attr = reverse
			else:
				attr = normal

			if context.empty:
				bg = red

			if context.directory:
				fg = blue
			elif context.executable:
				fg = green

			if context.media:
				fg = magenta

			if context.link:
				fg = cyan

			if context.maindisplay and context.selected:
				attr |= bold

		elif context.in_titlebar:
			attr |= bold

			if context.hostname:
				fg = green

			elif context.directory:
				fg = blue

			elif context.link:
				fg = cyan

		return fg, bg, attr
