# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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

import os
from curses import color_pair

import ranger
from ranger.gui.color import get_color
from ranger.gui.context import Context
from ranger.shared.settings import SettingsAware

# ColorScheme is not SettingsAware but it will gain access
# to the settings during the initialization.  We can't import
# SettingsAware here because of circular imports.

class ColorScheme(SettingsAware):
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
		keys = frozenset(keys)
		try:
			return self.cache[keys]

		except KeyError:
			context = Context(keys)

			# add custom error messages for broken colorschemes
			color = self.use(context)
			if self.settings.colorscheme_overlay:
				result = self.settings.colorscheme_overlay(context, *color)
				assert isinstance(result, (tuple, list)), \
						"Your colorscheme overlay doesn't return a tuple!"
				assert all(isinstance(val, int) for val in result), \
						"Your colorscheme overlay doesn't return a tuple"\
						" containing 3 integers!"
				color = result
			self.cache[keys] = color
			return color

	def get_attr(self, *keys):
		"""
		Returns the curses attribute for the specified keys

		Ready to use for curses.setattr()
		"""
		fg, bg, attr = self.get(*keys)
		return attr | color_pair(get_color(fg, bg))

	def use(self, context):
		"""
		Use the colorscheme to determine the (fg, bg, attr) tuple.

		When no colorscheme is found, ranger will fall back to this very
		basic colorscheme where directories are blue and bold, and
		selected files have the color inverted.

		Override this method in your own colorscheme.
		"""
		fg, attr = -1, 0
		if context.highlight or context.selected:
			attr = 262144
		if context.directory:
			attr |= 2097152
			fg = 4
		return fg, -1, attr

def _colorscheme_name_to_class(signal):
	# Find the colorscheme.  First look for it at ~/.ranger/colorschemes,
	# then at RANGERDIR/colorschemes.  If the file contains a class
	# named Scheme, it is used.  Otherwise, an arbitrary other class
	# is picked.
	if isinstance(signal.value, ColorScheme): return

	scheme_name = signal.value
	usecustom = not ranger.arg.clean

	def exists(colorscheme):
		return os.path.exists(colorscheme + '.py')

	def is_scheme(x):
		try:
			return issubclass(x, ColorScheme)
		except:
			return False

	# create ~/.ranger/colorschemes/__init__.py if it doesn't exist
	if usecustom:
		if os.path.exists(ranger.relpath_conf('colorschemes')):
			initpy = ranger.relpath_conf('colorschemes', '__init__.py')
			if not os.path.exists(initpy):
				open(initpy, 'a').close()

	if usecustom and \
			exists(ranger.relpath_conf('colorschemes', scheme_name)):
		scheme_supermodule = 'colorschemes'
	elif exists(ranger.relpath('colorschemes', scheme_name)):
		scheme_supermodule = 'ranger.colorschemes'
	else:
		scheme_supermodule = None  # found no matching file.

	if scheme_supermodule is None:
		# XXX: dont print while curses is running
		print("ERROR: colorscheme not found, fall back to builtin scheme")
		if ranger.arg.debug:
			raise Exception("Cannot locate colorscheme!")
		signal.value = ColorScheme()
	else:
		scheme_module = getattr(__import__(scheme_supermodule,
				globals(), locals(), [scheme_name], 0), scheme_name)
		if hasattr(scheme_module, 'Scheme') \
				and is_scheme(scheme_module.Scheme):
			signal.value = scheme_module.Scheme()
		else:
			for name, var in scheme_module.__dict__.items():
				if var != ColorScheme and is_scheme(var):
					signal.value = var()
					break
			else:
				raise Exception("The module contains no valid colorscheme!")
