from ranger.gui.colorscheme import ColorScheme
from ranger.gui.color import *

class Default(ColorScheme):
	def use(self, context):
		fg, bg, attr = default_colors

		if context.reset:
			pass

		elif context.in_browser:
			if context.selected:
				attr = reverse
			else:
				attr = normal

			if context.empty or context.error:
				bg = red

			if context.media:
				fg = magenta # fruits

			if context.container:
				fg = red # flowers

			if context.directory:
				fg = green # trees =)

			elif context.executable and not \
					any((context.media, context.container)):
				fg = yellow # banananas

			if context.link:
				fg = context.good and cyan or magenta

			if context.main_column and context.selected:
				attr |= bold

		elif context.in_titlebar:
			attr |= bold

			if context.hostname:
				fg = green

			elif context.directory:
				fg = blue

			elif context.link:
				fg = cyan

			elif context.keybuffer:
				fg = yellow
				attr = normal

		elif context.in_statusbar:
			if context.permissions or context.link:
				if context.good:
					fg = cyan
				elif context.bad:
					fg = magenta

		if context.text:
			if context.highlight:
				attr |= reverse
				fg = yellow

		if context.in_taskview:
			if context.title:
				fg = yellow
				attr |= reverse

			if context.selected:
				attr |= reverse

		return fg, bg, attr
