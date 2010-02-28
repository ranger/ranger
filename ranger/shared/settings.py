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

import types
from ranger.ext.openstruct import OpenStruct
from ranger.gui.colorscheme import ColorScheme

ALLOWED_SETTINGS = {
	'show_hidden': bool,
	'show_cursor': bool,
	'autosave_bookmarks': bool,
	'collapse_preview': bool,
	'sort': str,
	'reverse': bool,
	'directories_first': bool,
	'update_title': bool,
	'max_filesize_for_preview': (int, type(None)),
	'max_history_size': (int, type(None)),
	'scroll_offset': int,
	'preview_files': bool,
	'flushinput': bool,
	'colorscheme': (ColorScheme, types.ModuleType),
	'hidden_filter': lambda x: isinstance(x, str) or hasattr(x, 'match'),
}

# -- globalize the settings --
class SettingsAware(object):
	settings = OpenStruct()

	@staticmethod
	def _setup():
		from inspect import isclass, ismodule
		from ranger.gui.colorscheme import ColorScheme

		# overwrite single default options with custom options
		from ranger.defaults import options
		try:
			import options as custom_options
			for setting in ALLOWED_SETTINGS:
				if hasattr(custom_options, setting):
					setattr(options, setting, getattr(custom_options, setting))
				elif not hasattr(options, setting):
					raise Exception("This option was not defined: " + setting)
		except ImportError:
			pass

		assert check_option_types(options)

		try:
			import apps
		except ImportError:
			from ranger.defaults import apps

		try:
			import keys
		except ImportError:
			from ranger.defaults import keys


		# If a module is specified as the colorscheme, replace it with one
		# valid colorscheme inside that module.

		all_content = options.colorscheme.__dict__.items()

		if isclass(options.colorscheme) and \
				issubclass(options.colorscheme, ColorScheme):
			options.colorscheme = options.colorscheme()

		elif ismodule(options.colorscheme):
			def is_scheme(x):
				return isclass(x) and issubclass(x, ColorScheme)

			if hasattr(options.colorscheme, 'Scheme') \
					and is_scheme(options.colorscheme.Scheme):
				options.colorscheme = options.colorscheme.Scheme()
			else:
				for name, var in options.colorscheme.__dict__.items():
					if var != ColorScheme and is_scheme(var):
						options.colorscheme = var()
						break
				else:
					raise Exception("The module contains no " \
							"valid colorscheme!")
		else:
			raise Exception("Cannot locate colorscheme!")

		for setting in ALLOWED_SETTINGS:
			SettingsAware.settings[setting] = getattr(options, setting)

		SettingsAware.settings.keys = keys
		SettingsAware.settings.apps = apps


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
