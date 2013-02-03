# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

from inspect import isfunction
from ranger.ext.signals import SignalDispatcher
from ranger.core.shared import FileManagerAware
import re

ALLOWED_SETTINGS = {
	'autosave_bookmarks': bool,
	'autoupdate_cumulative_size': bool,
	'collapse_preview': bool,
	'colorscheme': str,
	'column_ratios': (tuple, list),
	'confirm_on_delete': str,
	'dirname_in_tabs': bool,
	'display_size_in_main_column': bool,
	'display_size_in_status_bar': bool,
	'display_tags_in_all_columns': bool,
	'draw_borders': bool,
	'draw_progress_bar_in_status_bar': bool,
	'flushinput': bool,
	'hidden_filter': (str, type(re.compile(""))), #COMPAT change to str-only
	'max_console_history_size': (int, type(None)),
	'max_history_size': (int, type(None)),
	'mouse_enabled': bool,
	'padding_right': bool,
	'preview_directories': bool,
	'preview_images': bool,
	'preview_files': bool,
	'preview_script': (str, type(None)),
	'save_console_history': bool,
	'scroll_offset': int,
	'shorten_title': int,  # XXX Note: False is an instance of int
	'show_cursor': bool,
	'show_hidden_bookmarks': bool,
	'show_hidden': bool,
	'status_bar_on_top': bool,
	'sort_case_insensitive': bool,
	'sort_directories_first': bool,
	'sort_reverse': bool,
	'sort': str,
	'tilde_in_titlebar': bool,
	'unicode_ellipsis': bool,
	'update_title': bool,
	'update_tmux_title': bool,
	'use_preview_script': bool,
	'xterm_alt_key': bool,
}

DEFAULT_VALUES = {
	bool: False,
	type(None): None,
	str: "",
	int: 0,
	list: [],
	tuple: tuple([]),
}

class SettingObject(SignalDispatcher, FileManagerAware):
	def __init__(self):
		SignalDispatcher.__init__(self)
		self.__dict__['_localsettings'] = dict()
		self.__dict__['_settings'] = dict()
		for name in ALLOWED_SETTINGS:
			self.signal_bind('setopt.'+name,
					self._raw_set_with_signal, priority=0.2)

	def set(self, name, value, path=None):
   		assert name in ALLOWED_SETTINGS, "No such setting: {0}!".format(name)
   		if name not in self._settings:
   			previous = None
   		else:
   			previous=self._settings[name]
   		assert self._check_type(name, value)
   		kws = dict(setting=name, value=value, previous=previous, path=path, fm=self.fm)
   		self.signal_emit('setopt', **kws)
   		self.signal_emit('setopt.'+name, **kws)

	def get(self, name, path=None):
		assert name in ALLOWED_SETTINGS, "No such setting: {0}!".format(name)
		if path and path in self._localsettings and name in self._localsettings[path]:
			return self._localsettings[path][name]
		elif name in self._settings:
			return self._settings[name]
		else:
			type_ = self.types_of(name)[0]
			value = DEFAULT_VALUES[type_]
			self._raw_set(name, value, None)
			self.__setattr__(name, value)
			return self._settings[name]

	def __setattr__(self, name, value):
		if name.startswith('_'):
			self.__dict__[name] = value
		else:
			self.set(name, value, None)

	def __getattr__(self, name):
		if name.startswith('_'):
			return self.__dict__[name]
		else:
			return self.get(name, None)

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
		typ = ALLOWED_SETTINGS[name]
		if isfunction(typ):
			assert typ(value), \
				"Warning: The option `" + name + "' has an incorrect type!"
		else:
			assert isinstance(value, typ), \
				"Warning: The option `" + name + "' has an incorrect type!"\
				" Got " + str(type(value)) + ", expected " + str(typ) + "!" +\
				" Please check if your commands.py is up to date." if not \
				self.fm.ui.is_set_up else ""
		return True

	__getitem__ = __getattr__
	__setitem__ = __setattr__

	def _raw_set(self, name, value, path):
		if path:
			if not path in self._localsettings:
				self._localsettings[path] = dict()
			self._localsettings[path][name] = value

			# make sure name is in _settings, so __iter__ runs through local settigns too.
			if not name in self._settings:
				type_ = self.types_of(name)[0]
				value = DEFAULT_VALUES[type_]
				self._settings[name] = value
		else:
			self._settings[name] = value

	def _raw_set_with_signal(self, signal):
		self._raw_set(signal.setting, signal.value, signal.path)


class LocalSettingObject():
	def __init__(self, path, parent):
		self.__dict__['_parent'] = parent
		self.__dict__['_path'] = path

	def __setattr__(self, name, value):
		if name.startswith('_'):
			self.__dict__[name] = value
		else:
			self._parent.set(name, value, self._path)

	def __getattr__(self, name):
		if name.startswith('_'):
			return self.__dict__[name]
		else:
			return self._parent.get(name, self._path)

	def __iter__(self):
		for x in self._parent._settings:
			yield x

	__getitem__ = __getattr__
	__setitem__ = __setattr__
