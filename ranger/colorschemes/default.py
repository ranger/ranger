from ranger.gui.colorscheme import ColorScheme
from ranger.gui.color import *

class Default(ColorScheme):
	def use(self, context):
		fg, bg, attr = default_colors

		if context.reset:
			pass

		elif context.in_display:
			if context.selected:
				attr = reverse
			else:
				attr = normal

			if context.empty or context.error:
				bg = red

			if context.media:
				if context.image:
					fg = yellow
				else:
					fg = magenta

			if context.container:
				fg = red

			if context.document:
				fg = default

			if context.directory:
				fg = blue

			elif context.executable and not any((context.media, context.container, context.document)):
				attr |= bold
				fg = green

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
