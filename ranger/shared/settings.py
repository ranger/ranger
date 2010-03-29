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

import os
import types
from inspect import isclass, ismodule
import ranger
from ranger.ext.openstruct import OpenStruct
from ranger.gui.colorscheme import ColorScheme

ALLOWED_SETTINGS = {
	'show_hidden': bool,
	'show_cursor': bool,
	'autosave_bookmarks': bool,
	'save_console_history': bool,
	'collapse_preview': bool,
	'draw_borders': bool,
	'draw_bookmark_borders': bool,
	'sort': str,
	'sort_reverse': bool,
	'sort_case_insensitive': bool,
	'sort_directories_first': bool,
	'update_title': bool,
	'shorten_title': int,  # Note: False is an instance of int
	'max_filesize_for_preview': (int, type(None)),
	'max_history_size': (int, type(None)),
	'scroll_offset': int,
	'preview_files': bool,
	'preview_directories': bool,
	'flushinput': bool,
	'colorscheme': str,
	'colorscheme_overlay': (type(None), type(lambda:0)),
	'hidden_filter': lambda x: isinstance(x, str) or hasattr(x, 'match'),
}

COMPAT_MAP = {
	'sort_reverse': 'reverse',
	'sort_directories_first': 'directories_first',
}

# -- globalize the settings --
class SettingsAware(object):
	settings = OpenStruct()

	@staticmethod
	def _setup():
		settings = OpenStruct()

		from ranger.defaults import options
		for setting in ALLOWED_SETTINGS:
			try:
				settings[setting] = getattr(options, setting)
			except AttributeError:
				raise Exception("The option `{0}' was not defined" \
						" in the defaults!".format(setting))

		import sys
		if not ranger.arg.clean:
			# overwrite single default options with custom options
			try:
				import options as my_options
			except ImportError:
				pass
			else:
				for setting in ALLOWED_SETTINGS:
					try:
						settings[setting] = getattr(my_options, setting)
					except AttributeError:
						pass
				for new, old in COMPAT_MAP.items():
					try:
						settings[new] = getattr(my_options, old)
						print("Warning: the option `{0}'"\
								" was renamed to `{1}'\nPlease update"\
								" your configuration file soon." \
								.format(old, new))
					except AttributeError:
						pass

		assert check_option_types(settings)

		# Find the colorscheme.  First look for it at ~/.ranger/colorschemes,
		# then at RANGERDIR/colorschemes.  If the file contains a class
		# named Scheme, it is used.  Otherwise, an arbitrary other class
		# is picked.

		scheme_name = settings.colorscheme

		def exists(colorscheme):
			return os.path.exists(colorscheme + '.py')

		def is_scheme(x):
			return isclass(x) and issubclass(x, ColorScheme)

		# create ~/.ranger/colorschemes/__init__.py if it doesn't exist
		if os.path.exists(ranger.relpath_conf('colorschemes')):
			initpy = ranger.relpath_conf('colorschemes', '__init__.py')
			if not os.path.exists(initpy):
				open(initpy, 'a').close()

		if exists(ranger.relpath_conf('colorschemes', scheme_name)):
			scheme_supermodule = 'colorschemes'
		elif exists(ranger.relpath('colorschemes', scheme_name)):
			scheme_supermodule = 'ranger.colorschemes'
		else:
			scheme_supermodule = None  # found no matching file.

		if scheme_supermodule is None:
			print("ERROR: colorscheme not found, fall back to builtin scheme")
			if ranger.arg.debug:
				raise Exception("Cannot locate colorscheme!")
			settings.colorscheme = ColorScheme()
		else:
			scheme_module = getattr(__import__(scheme_supermodule,
					globals(), locals(), [scheme_name], 0), scheme_name)
			assert ismodule(scheme_module)
			if hasattr(scheme_module, 'Scheme') \
					and is_scheme(scheme_module.Scheme):
				settings.colorscheme = scheme_module.Scheme()
			else:
				for name, var in scheme_module.__dict__.items():
					if var != ColorScheme and is_scheme(var):
						settings.colorscheme = var()
						break
				else:
					raise Exception("The module contains no " \
							"valid colorscheme!")

		# Making the colorscheme SettingsAware doesn't work because
		# of circular imports, so we do it like this:
		settings.colorscheme.settings = settings  

		try:
			import apps
		except ImportError:
			from ranger.defaults import apps
		settings.apps = apps
		try:
			import keys
		except ImportError:
			from ranger.defaults import keys
		settings.keys = keys

		SettingsAware.settings = settings

def check_option_types(opt):
	import inspect
	for name, typ in ALLOWED_SETTINGS.items():
		optvalue = getattr(opt, name)
		if inspect.isfunction(typ):
			assert typ(optvalue), \
				"The option `" + name + "' has an incorrect type!"
		else:
			assert isinstance(optvalue, typ), \
				"The option `" + name + "' has an incorrect type!"\
				" Got " + str(type(optvalue)) + ", expected " + str(typ) + "!"
	return True
