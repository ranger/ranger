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
				if context.image:
					fg = yellow
				else:
					fg = magenta

			if context.container:
				fg = red

#			if context.document:
#				fg = default

			if context.directory:
				fg = blue

			elif context.executable and not \
					any((context.media, context.container)):
				attr |= bold
				fg = green

			if context.link:
				fg = context.good and cyan or magenta

			if context.tag_marker and not context.selected:
				attr |= bold
				if fg in (red, magenta):
					fg = white
				else:
					fg = red

			if context.main_column:
				if context.selected:
					attr |= bold
				if context.marked:
					attr |= bold
					fg = yellow

		elif context.in_titlebar:
			attr |= bold

			if context.hostname:
				fg = green

			elif context.directory:
				fg = blue

			elif context.link:
				fg = cyan

		elif context.in_statusbar:
			if context.permissions:
				if context.good:
					fg = cyan
				elif context.bad:
					fg = magenta
			if context.marked:
				attr |= bold | reverse
				fg = yellow
			if context.message:
				if context.bad:
					attr |= bold
					fg = red

		if context.in_pager or context.help_markup:
			if context.seperator:
				fg = red
			elif context.link:
				fg = cyan
			elif context.bars:
				fg = black
				attr |= bold
			elif context.quotes or context.text:
				fg = magenta
			elif context.key:
				fg = green
			elif context.special:
				fg = cyan
			elif context.title:
				attr |= bold

		if context.text:
			if context.highlight:
				attr |= reverse

		if context.in_taskview:
			if context.title:
				fg = blue

			if context.selected:
				attr |= reverse

		return fg, bg, attr
