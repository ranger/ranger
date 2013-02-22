# Copyright (C) 2009-2013  Roman Zimbelmann <hut@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

# THIS WHOLE FILE IS OBSOLETE AND EXISTS FOR BACKWARDS COMPATIBILITIY

import os
from ranger.ext.signals import SignalDispatcher
from ranger.core.shared import SettingsAware, FileManagerAware

# COMPAT
class Environment(SettingsAware, FileManagerAware, SignalDispatcher):
    def __init__(self, path):
        SignalDispatcher.__init__(self)

    def _get_copy(self): return self.fm.copy_buffer
    def _set_copy(self, obj): self.fm.copy_buffer = obj
    copy = property(_get_copy, _set_copy)

    def _get_cut(self): return self.fm.do_cut
    def _set_cut(self, obj): self.fm.do_cut = obj
    cut = property(_get_cut, _set_cut)

    def _get_keymaps(self): return self.fm.ui.keymaps
    def _set_keymaps(self, obj): self.fm.ui.keymaps = obj
    keymaps = property(_get_keymaps, _set_keymaps)

    def _get_keybuffer(self): return self.fm.ui.keybuffer
    def _set_keybuffer(self, obj): self.fm.ui.keybuffer = obj
    keybuffer = property(_get_keybuffer, _set_keybuffer)

    def _get_username(self): return self.fm.username
    def _set_username(self, obj): self.fm.username = obj
    username = property(_get_username, _set_username)

    def _get_hostname(self): return self.fm.hostname
    def _set_hostname(self, obj): self.fm.hostname = obj
    hostname = property(_get_hostname, _set_hostname)

    def _get_home_path(self): return self.fm.home_path
    def _set_home_path(self, obj): self.fm.home_path = obj
    home_path = property(_get_home_path, _set_home_path)

    def _get_get_directory(self): return self.fm.get_directory
    def _set_get_directory(self, obj): self.fm.get_directory = obj
    get_directory = property(_get_get_directory, _set_get_directory)

    def _get_garbage_collect(self): return self.fm.garbage_collect
    def _set_garbage_collect(self, obj): self.fm.garbage_collect = obj
    garbage_collect = property(_get_garbage_collect, _set_garbage_collect)

    def _get_cwd(self): return self.fm.thisdir
    def _set_cwd(self, obj): self.fm.thisdir = obj
    cwd = property(_get_cwd, _set_cwd)

    def _get_cf(self): return self.fm.thisfile
    def _set_cf(self, obj): self.fm.thisfile = obj
    cf = property(_get_cf, _set_cf)

    def _get_history(self): return self.fm.thistab.history
    def _set_history(self, obj): self.fm.thistab.history = obj
    history = property(_get_history, _set_history)

    def _get_last_search(self): return self.fm.thistab.last_search
    def _set_last_search(self, obj): self.fm.thistab.last_search = obj
    last_search = property(_get_last_search, _set_last_search)

    def _get_path(self): return self.fm.thistab.path
    def _set_path(self, obj): self.fm.thistab.path = obj
    path = property(_get_path, _set_path)

    def _get_pathway(self): return self.fm.thistab.pathway
    def _set_pathway(self, obj): self.fm.thistab.pathway = obj
    pathway = property(_get_pathway, _set_pathway)

    def _get_enter_dir(self): return self.fm.thistab.enter_dir
    def _set_enter_dir(self, obj): self.fm.thistab.enter_dir = obj
    enter_dir = property(_get_enter_dir, _set_enter_dir)

    def _get_at_level(self): return self.fm.thistab.at_level
    def _set_at_level(self, obj): self.fm.thistab.at_level = obj
    at_level = property(_get_at_level, _set_at_level)

    def _get_get_selection(self): return self.fm.thistab.get_selection
    def _set_get_selection(self, obj): self.fm.thistab.get_selection = obj
    get_selection = property(_get_get_selection, _set_get_selection)

    def _get_assign_cursor_positions_for_subdirs(self):
        return self.fm.thistab.assign_cursor_positions_for_subdirs
    def _set_assign_cursor_positions_for_subdirs(self, obj):
        self.fm.thistab.assign_cursor_positions_for_subdirs = obj
    assign_cursor_positions_for_subdirs = property(
            _get_assign_cursor_positions_for_subdirs,
            _set_assign_cursor_positions_for_subdirs)

    def _get_ensure_correct_pointer(self):
        return self.fm.thistab.ensure_correct_pointer
    def _set_ensure_correct_pointer(self, obj):
        self.fm.thistab.ensure_correct_pointer = obj
    ensure_correct_pointer = property(_get_ensure_correct_pointer,
            _set_ensure_correct_pointer)

    def _get_history_go(self): return self.fm.thistab.history_go
    def _set_history_go(self, obj): self.fm.thistab.history_go = obj
    history_go = property(_get_history_go, _set_history_go)

    def _set_cf_from_signal(self, signal):
        self.fm._cf = signal.new

    def get_free_space(self, path):
        stat = os.statvfs(path)
        return stat.f_bavail * stat.f_bsize
