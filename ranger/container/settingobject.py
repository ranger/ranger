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
	'preview_files': bool,
	'preview_script': (str, type(None)),
	'save_console_history': bool,
	'scroll_offset': int,
	'shorten_title': int,  # XXX Note: False is an instance of int
	'show_cursor': bool,
	'show_hidden_bookmarks': bool,
	'show_hidden': bool,
	'sort_case_insensitive': bool,
	'sort_directories_first': bool,
	'sort_reverse': bool,
	'sort': str,
	'tilde_in_titlebar': bool,
	'unicode_ellipsis': bool,
	'update_title': bool,
	'use_preview_script': bool,
	'xterm_alt_key': bool,
}

DEFAULT_VALUES = {
	bool: False,
	type(None): None,
	str: "",
	int: 0,
	list: [],
}

class SettingObject(SignalDispatcher, FileManagerAware):
	def __init__(self):
		SignalDispatcher.__init__(self)
		self.__dict__['_settings'] = dict()
		for name in ALLOWED_SETTINGS:
			self.signal_bind('setopt.'+name,
					self._raw_set_with_signal, priority=0.2)

	def __setattr__(self, name, value):
		if name[0] == '_':
			self.__dict__[name] = value
		else:
			assert name in ALLOWED_SETTINGS, "No such setting: {0}!".format(name)
			if name not in self._settings:
				previous = None
			else:
				previous=self._settings[name]
			assert self._check_type(name, value)
			kws = dict(setting=name, value=value, previous=previous, fm=self.fm)
			self.signal_emit('setopt', **kws)
			self.signal_emit('setopt.'+name, **kws)

	def __getattr__(self, name):
		assert name in ALLOWED_SETTINGS or name in self._settings, \
				"No such setting: {0}!".format(name)
		if name.startswith('_'):
			return self.__dict__[name]
		try:
			return self._settings[name]
		except:
			type_ = self.types_of(name)[0]
			value = DEFAULT_VALUES[type_]
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
