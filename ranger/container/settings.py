# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

import re
import os.path
from inspect import isfunction

import ranger
from ranger.ext.signals import SignalDispatcher
from ranger.core.shared import FileManagerAware
from ranger.gui.colorscheme import _colorscheme_name_to_class

# Use these priority constants to trigger events at specific points in time
# during processing of the signals "setopt" and "setopt.<some_setting_name>"
# pylint: disable=bad-whitespace
SIGNAL_PRIORITY_RAW        = 2.0  # signal.value will be raw
SIGNAL_PRIORITY_SANITIZE   = 1.0  # (Internal) post-processing signal.value
SIGNAL_PRIORITY_BETWEEN    = 0.6  # sanitized signal.value, old fm.settings.XYZ
SIGNAL_PRIORITY_SYNC       = 0.2  # (Internal) updating fm.settings.XYZ
SIGNAL_PRIORITY_AFTER_SYNC = 0.1  # after fm.settings.XYZ was updated
# pylint: enable=bad-whitespace


ALLOWED_SETTINGS = {
    'automatically_count_files': bool,
    'autosave_bookmarks': bool,
    'autoupdate_cumulative_size': bool,
    'cd_bookmarks': bool,
    'cd_tab_case': str,
    'cd_tab_smart': bool,
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
    'hidden_filter': str,
    'idle_delay': int,
    'line_numbers': str,
    'max_console_history_size': (int, type(None)),
    'max_history_size': (int, type(None)),
    'metadata_deep_search': bool,
    'mouse_enabled': bool,
    'open_all_images': bool,
    'padding_right': bool,
    'preview_directories': bool,
    'preview_files': bool,
    'preview_images': bool,
    'preview_images_method': str,
    'preview_max_size': int,
    'preview_script': (str, type(None)),
    'save_console_history': bool,
    'scroll_offset': int,
    'shorten_title': int,
    'show_cursor': bool,  # TODO: not working?
    'show_selection_in_titlebar': bool,
    'show_hidden_bookmarks': bool,
    'show_hidden': bool,
    'sort_case_insensitive': bool,
    'sort_directories_first': bool,
    'sort_reverse': bool,
    'sort_unicode': bool,
    'sort': str,
    'status_bar_on_top': bool,
    'hostname_in_titlebar': bool,
    'tilde_in_titlebar': bool,
    'unicode_ellipsis': bool,
    'update_title': bool,
    'update_tmux_title': bool,
    'use_preview_script': bool,
    'viewmode': str,
    'vcs_aware': bool,
    'vcs_backend_bzr': str,
    'vcs_backend_git': str,
    'vcs_backend_hg': str,
    'vcs_backend_svn': str,
    'wrap_scroll': bool,
    'xterm_alt_key': bool,
    'clear_filters_on_dir_change': bool,
    'save_tabs_on_exit': bool,
}

ALLOWED_VALUES = {
    'cd_tab_case': ['sensitive', 'insensitive', 'smart'],
    'confirm_on_delete': ['multiple', 'always', 'never'],
    'line_numbers': ['false', 'absolute', 'relative'],
    'preview_images_method': ['w3m', 'iterm2', 'urxvt', 'urxvt-full'],
    'vcs_backend_bzr': ['disabled', 'local', 'enabled'],
    'vcs_backend_git': ['enabled', 'disabled', 'local'],
    'vcs_backend_hg': ['disabled', 'local', 'enabled'],
    'vcs_backend_svn': ['disabled', 'local', 'enabled'],
    'viewmode': ['miller', 'multipane'],
}

DEFAULT_VALUES = {
    bool: False,
    type(None): None,
    str: "",
    int: 0,
    list: [],
    tuple: tuple([]),
}


class Settings(SignalDispatcher, FileManagerAware):

    def __init__(self):
        SignalDispatcher.__init__(self)
        self.__dict__['_localsettings'] = dict()
        self.__dict__['_localregexes'] = dict()
        self.__dict__['_tagsettings'] = dict()
        self.__dict__['_settings'] = dict()
        for name in ALLOWED_SETTINGS:
            self.signal_bind('setopt.' + name, self._sanitize,
                             priority=SIGNAL_PRIORITY_SANITIZE)
            self.signal_bind('setopt.' + name, self._raw_set_with_signal,
                             priority=SIGNAL_PRIORITY_SYNC)
        for name, values in ALLOWED_VALUES.items():
            assert values
            assert name in ALLOWED_SETTINGS
            self._raw_set(name, values[0])

    def _sanitize(self, signal):
        name, value = signal.setting, signal.value
        if name == 'column_ratios':
            # TODO: cover more cases here
            if isinstance(value, tuple):
                signal.value = list(value)
            if not isinstance(value, list) or len(value) < 2:
                signal.value = [1, 1]
            else:
                signal.value = [int(i) if str(i).isdigit() else 1
                                for i in value]

        elif name == 'colorscheme':
            _colorscheme_name_to_class(signal)

        elif name == 'preview_script':
            if isinstance(value, str):
                result = os.path.expanduser(value)
                if os.path.exists(result):
                    signal.value = result
                else:
                    self.fm.notify("Preview script `{0}` doesn't exist!".format(result), bad=True)
                    signal.value = None

        elif name == 'use_preview_script':
            if self._settings.get('preview_script') is None and value and self.fm.ui.is_on:
                self.fm.notify("Preview script undefined or not found!",
                               bad=True)

    def set(self, name, value, path=None, tags=None):
        assert name in ALLOWED_SETTINGS, "No such setting: {0}!".format(name)
        if name not in self._settings:
            previous = None
        else:
            previous = self._settings[name]
        assert self._check_type(name, value)
        assert not (tags and path), "Can't set a setting for path and tag " \
            "at the same time!"
        kws = dict(setting=name, value=value, previous=previous,
                   path=path, tags=tags, fm=self.fm)
        self.signal_emit('setopt', **kws)
        self.signal_emit('setopt.' + name, **kws)

    def _get_default(self, name):
        if name == 'preview_script':
            if ranger.args.clean:
                value = self.fm.relpath('data/scope.sh')
            else:
                value = self.fm.confpath('scope.sh')
                if not os.path.exists(value):
                    value = self.fm.relpath('data/scope.sh')
        else:
            value = DEFAULT_VALUES[self.types_of(name)[0]]

        return value

    def get(self, name, path=None):
        assert name in ALLOWED_SETTINGS, "No such setting: {0}!".format(name)
        if path:
            localpath = path
        else:
            try:
                localpath = self.fm.thisdir.path
            except AttributeError:
                localpath = None

        if localpath:
            for pattern, regex in self._localregexes.items():
                if name in self._localsettings[pattern] and\
                        regex.search(localpath):
                    return self._localsettings[pattern][name]

        if self._tagsettings and path:
            realpath = os.path.realpath(path)
            if realpath in self.fm.tags:
                tag = self.fm.tags.marker(realpath)
                if tag in self._tagsettings and name in self._tagsettings[tag]:
                    return self._tagsettings[tag][name]

        if name not in self._settings:
            value = self._get_default(name)
            self._raw_set(name, value)
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
        return self.get(name, None)

    def __iter__(self):
        for setting in self._settings:
            yield setting

    @staticmethod
    def types_of(name):
        try:
            typ = ALLOWED_SETTINGS[name]
        except KeyError:
            return tuple()
        else:
            if isinstance(typ, tuple):
                return typ
            return (typ,)

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

    def _raw_set(self, name, value, path=None, tags=None):
        if path:
            if path not in self._localsettings:
                try:
                    regex = re.compile(path)
                except re.error:  # Bad regular expression
                    return
                self._localregexes[path] = regex
                self._localsettings[path] = dict()
            self._localsettings[path][name] = value

            # make sure name is in _settings, so __iter__ runs through
            # local settings too.
            if name not in self._settings:
                type_ = self.types_of(name)[0]
                value = DEFAULT_VALUES[type_]
                self._settings[name] = value
        elif tags:
            for tag in tags:
                if tag not in self._tagsettings:
                    self._tagsettings[tag] = dict()
                self._tagsettings[tag][name] = value
        else:
            self._settings[name] = value

    def _raw_set_with_signal(self, signal):
        self._raw_set(signal.setting, signal.value, signal.path, signal.tags)


class LocalSettings(object):  # pylint: disable=too-few-public-methods

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
        return self._parent.get(name, self._path)

    def __iter__(self):
        for setting in self._parent._settings:  # pylint: disable=protected-access
            yield setting

    __getitem__ = __getattr__
    __setitem__ = __setattr__
