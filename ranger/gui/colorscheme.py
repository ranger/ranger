"""
Colorschemes define colors for specific contexts.

Generally, this works by passing a set of keywords (strings) to
the colorscheme.get() method to receive the tuple (fg, bg, attr).
fg, bg are the foreground and background colors and attr is the attribute.
The values are specified in ranger.gui.color.

A colorscheme must...

1. be inside either of these directories:
~/.ranger/colorschemes/
path/to/ranger/colorschemes/

2. be a subclass of ranger.gui.colorscheme.ColorScheme

3. implement a use(self, context) method which returns (fg, bg, attr).
context is a struct which contains all entries of CONTEXT_KEYS,
associated with either True or False.

define which colorscheme to use by having this to your options.py:
from ranger import colorschemes
colorscheme = colorschemes.filename

If your colorscheme-file contains more than one colorscheme, specify it with:
colorscheme = colorschemes.filename.classname
"""

from ranger.ext.openstruct import OpenStruct

CONTEXT_KEYS = [ 'reset', 'error',
		'in_browser', 'in_statusbar', 'in_titlebar', 'in_console',
		'in_pager', 'in_taskview',
		'directory', 'file', 'hostname',
		'executable', 'media', 'link',
		'video', 'audio', 'image', 'media', 'document', 'container',
		'selected', 'empty', 'main_column', 'message', 'background',
		'good', 'bad',
		'space', 'permissions', 'owner', 'group', 'mtime', 'nlink',
		'scroll', 'all', 'bot', 'top', 'percentage',
		'marked', 'tagged', 'tag_marker',
		'help_markup',
		'seperator', 'key', 'special',
		'title', 'text', 'highlight', 'bars', 'quotes',
		'keybuffer']

class ColorScheme(object):
	"""
	This is the class that colorschemes must inherit from.

	it defines get() 
	it defines the get() method, which returns the color tuple
	which fits to the given keys.
	"""

	def __init__(self):
		self.cache = {}

	def get(self, *keys):
		"""
		Returns the (fg, bg, attr) for the given keys.

		Using this function rather than use() will cache all
		colors for faster access.
		"""
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
		"""
		Returns the curses attribute for the specified keys
		
		Ready to use for curses.setattr()
		"""
		from curses import color_pair
		from ranger.gui.color import get_color

		fg, bg, attr = self.get(*keys)
		return attr | color_pair(get_color(fg, bg))

	def use(self, context):
		"""
		Use the colorscheme to determine the (fg, bg, attr) tuple.
		This is a dummy function which always returns default_colors.
		Override this in your custom colorscheme!
		"""
		from ranger.gui.color import default_colors

		return default_colors
