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

import ranger
from ranger.ext.signal_dispatcher import SignalDispatcher
from ranger.ext.openstruct import OpenStruct

ALLOWED_SETTINGS = {
	'show_hidden': bool,
	'show_hidden_bookmarks': bool,
	'show_cursor': bool,
	'autosave_bookmarks': bool,
	'save_console_history': bool,
	'collapse_preview': bool,
	'column_ratios': (tuple, list, set),
	'display_size_in_main_column': bool,
	'display_size_in_status_bar': bool,
	'draw_borders': bool,
	'draw_bookmark_borders': bool,
	'sort': str,
	'sort_reverse': bool,
	'sort_case_insensitive': bool,
	'sort_directories_first': bool,
	'update_title': bool,
	'shorten_title': int,  # Note: False is an instance of int
	'tilde_in_titlebar': bool,
	'max_filesize_for_preview': (int, type(None)),
	'max_history_size': (int, type(None)),
	'scroll_offset': int,
	'preview_files': bool,
	'preview_directories': bool,
	'mouse_enabled': bool,
	'flushinput': bool,
	'colorscheme': str,
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
		for name in ALLOWED_SETTINGS:
			self.signal_bind('setopt.'+name,
					self._raw_set_with_signal, priority=0.2)

	def __setattr__(self, name, value):
		if name[0] == '_':
			self.__dict__[name] = value
		else:
			assert name in self._settings, "No such setting: {0}!".format(name)
			assert self._check_type(name, value)
			kws = dict(setting=name, value=value,
					previous=self._settings[name])
			self.signal_emit('setopt', **kws)
			self.signal_emit('setopt.'+name, **kws)

	def __getattr__(self, name):
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
			self._raw_set(name, value)
			self.__setattr__(name, value)
			return self._settings[name]

	def __iter__(self):
		for x in self._settings:
			yield x

	def types_of(self, name):
		try:
			typ = ALLOWED_SETTINGS[name]
		except KeyError:
			return tuple()
		else:
			if isinstance(typ, tuple):
				return typ
			else:
				return (typ, )


	def _check_type(self, name, value):
		from inspect import isfunction
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

	def _raw_set(self, name, value):
		self._settings[name] = value

	def _raw_set_with_signal(self, signal):
		self._settings[signal.setting] = signal.value


# -- globalize the settings --
class SettingsAware(object):
	settings = OpenStruct()

	@staticmethod
	def _setup():
		settings = SettingObject()

		from ranger.gui.colorscheme import _colorscheme_name_to_class
		settings.signal_bind('setopt.colorscheme',
				_colorscheme_name_to_class, priority=1)

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

		from ranger.defaults import options as default_options
		settings._setting_sources.append(default_options)
		assert all(hasattr(default_options, setting) \
				for setting in ALLOWED_SETTINGS), \
				"Ensure that all options are defined in the defaults!"

		try:
			import apps
		except ImportError:
			from ranger.defaults import apps
		settings._raw_set('apps', apps)
		try:
			import keys
		except ImportError:
			from ranger.defaults import keys
		settings._raw_set('keys', keys)

		SettingsAware.settings = settings
