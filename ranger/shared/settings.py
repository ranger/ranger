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
from inspect import isclass, ismodule, isfunction
import ranger
from ranger.ext.signal_dispatcher import SignalDispatcher
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
	'colorscheme': (str, ColorScheme),
	'colorscheme_overlay': (type(None), type(lambda:0)),
	'hidden_filter': lambda x: isinstance(x, str) or hasattr(x, 'match'),
}

COMPAT_MAP = {
	'sort_reverse': 'reverse',
	'sort_directories_first': 'directories_first',
}


class SettingObject(SignalDispatcher):
	def __init__(self):
		SignalDispatcher.__init__(self)
		self.__dict__['_settings'] = dict()
		self.__dict__['_setting_sources'] = list()
		self.signal_bind('core.setting',
				self._setting_set_raw_signal, priority=0.2)

	def __setattr__(self, name, value):
		if name[0] == '_':
			self.__dict__[name] = value
		else:
			assert name in self._settings, "No such setting: {0}!".format(name)
			assert self._check_type(name, value)
			kws = dict(setting=name, value=value,
					previous=self._settings[name])
			self.signal_emit('core.setting', **kws)
			self.signal_emit('core.setting.'+name, **kws)

	def __getattr__(self, name):
#		if name[0] == '_':
#			return getattr(self, name)
		assert name in ALLOWED_SETTINGS or name in self._settings, \
				"No such setting: {0}!".format(name)
		try:
			return self._settings[name]
		except:
			for struct in self._setting_sources:
				try: value = getattr(struct, name)
				except: pass
				else: break
			else:
				raise Exception("The option `{0}' was not defined" \
						" in the defaults!".format(name))
			assert self._check_type(name, value)
			self._raw_set_setting(name, value)
			self.__setattr__(name, value)
			return self._settings[name]

	def _check_type(self, name, value):
		typ = ALLOWED_SETTINGS[name]
		if isfunction(typ):
			assert typ(value), \
				"The option `" + name + "' has an incorrect type!"
		else:
			assert isinstance(value, typ), \
				"The option `" + name + "' has an incorrect type!"\
				" Got " + str(type(value)) + ", expected " + str(typ) + "!"
		return True

	__getitem__ = __getattr__
	__setitem__ = __setattr__

	def _raw_set_setting(self, name, value):
		self._settings[name] = value

	def _setting_set_raw_signal(self, signal):
		self._settings[signal.setting] = signal.value

def _colorscheme_name_to_class(signal):
	# Find the colorscheme.  First look for it at ~/.ranger/colorschemes,
	# then at RANGERDIR/colorschemes.  If the file contains a class
	# named Scheme, it is used.  Otherwise, an arbitrary other class
	# is picked.
	if not signal.setting == 'colorscheme': return
	if isinstance(signal.value, ColorScheme): return

	scheme_name = signal.value
	usecustom = not ranger.arg.clean

	def exists(colorscheme):
		return os.path.exists(colorscheme + '.py')

	def is_scheme(x):
		return isclass(x) and issubclass(x, ColorScheme)

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
		assert ismodule(scheme_module)
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

	# Making the colorscheme "SettingsAware" doesn't work because
	# of circular imports, so we do it like this:
	signal.value.settings = signal.origin


# -- globalize the settings --
class SettingsAware(object):
	settings = OpenStruct()

	@staticmethod
	def _setup():
		settings = SettingObject()
		settings.signal_bind('core.setting',
				_colorscheme_name_to_class, priority=1)

		from ranger.defaults import options as default_options
		settings._setting_sources.append(default_options)
		assert all(hasattr(default_options, setting) \
				for setting in ALLOWED_SETTINGS), \
				"Ensure that all options are defined in the defaults!"

		if not ranger.arg.clean:
			# overwrite single default options with custom options
			try:
				import options as my_options
			except ImportError:
				pass
			else:
				settings._setting_sources.append(my_options)

				# For backward compatibility:
				for new, old in COMPAT_MAP.items():
					try:
						setattr(my_options, new, getattr(my_options, old))
						print("Warning: the option `{0}'"\
								" was renamed to `{1}'\nPlease update"\
								" your configuration file soon." \
								.format(old, new))
					except AttributeError:
						pass

		try:
			import apps
		except ImportError:
			from ranger.defaults import apps
		settings._raw_set_setting('apps', apps)
		try:
			import keys
		except ImportError:
			from ranger.defaults import keys
		settings._raw_set_setting('keys', keys)

		SettingsAware.settings = settings
