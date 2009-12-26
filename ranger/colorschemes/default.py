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

			if context.maindisplay:
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

		elif context.in_notify:
			attr |= reverse
#			if context.good:
#				bg = cyan
#			else:
#				bg = red
#			if context.message:
#				attr |= bold
#				fg = white

		if context.text:
			if context.highlight:
				attr |= reverse

		if context.in_pman:
			if context.title:
				fg = blue

			if context.selected:
				attr |= reverse

		return fg, bg, attr
