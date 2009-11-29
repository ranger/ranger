from ranger.gui.colorscheme import ColorScheme
from ranger.gui.color import *

class Snow(ColorScheme):
	def use(self, context):
		if context.reset:
			return default_colors

		if context.wdisplay:
			fg, bg = default, default

			if context.selected:
				attr = reverse
			else:
				attr = normal

			if context.empty:
				bg = red

			if context.directory:
				fg = blue

			if context.executable:
				fg = green

			if context.media:
				fg = pink

			if context.link:
				fg = cyan

			if context.maindisplay and context.selected:
				attr = attr | bold
				fg = yellow

			return fg, bg, attr

		return default_colors
