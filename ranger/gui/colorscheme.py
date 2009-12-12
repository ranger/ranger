CONTEXT_KEYS = [ 'reset', 'error',
		'in_display', 'in_statusbar', 'in_titlebar', 'in_console',
		'directory', 'file', 'hostname',
		'executable', 'media', 'link',
		'video', 'audio', 'image', 'media', 'document', 'container',
		'broken', 'selected', 'empty', 'maindisplay',
		'keybuffer']

# colorscheme specification:
#
# A colorscheme must...
#
# 1. be inside either of these directories:
# ~/.ranger/colorschemes/
# path/to/ranger/colorschemes/
#
# 2. be a subclass ofranger.gui.colorscheme.ColorScheme
# 
# 3. have a use(self, context) method which returns a tuple of 3 integers.
# the first integer is the foreground color, the second is the background
# color, the third is the attribute, as specified by the curses module.
#
#
# define which colorscheme to use by having this to your options.py:
# from ranger import colorschemes
# colorscheme = colorschemes.filename
# 
# If your colorscheme-file contains more than one colorscheme, specify it with:
# colorscheme = colorschemes.filename.classname

from ranger.ext.openstruct import OpenStruct

class ColorScheme(object):
	def __init__(self):
		self.cache = {}

	def get(self, *keys):
		"""Determine the (fg, bg, attr) tuple or get it from cache"""
		try:
			return self.cache[keys]

		except KeyError:
			context = OpenStruct()

			for key in CONTEXT_KEYS:
				context[key] = (key in keys)

			# add custom error messages for broken colorschemes
			color = self.use(context)
			self.cache[keys] = color
			return color

	def get_attr(self, *keys):
		"""Returns the curses attr integer for the specified keys"""
		from ranger.gui.color import get_color
		import curses

		fg, bg, attr = self.get(*keys)
		return attr | curses.color_pair(get_color(fg, bg))


	def use(self, context):
		"""Use the colorscheme to determine the (fg, bg, attr) tuple.
This is a dummy function which always returns default_colors.
Override this in your custom colorscheme!"""
		from ranger.gui.color import default_colors
		return default_colors

