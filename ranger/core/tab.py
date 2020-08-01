# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

import os
from os.path import abspath, normpath, join, expanduser, isdir, dirname

from ranger import PY3
from ranger.container import settings
from ranger.container.history import History
from ranger.core.shared import FileManagerAware, SettingsAware


class Tab(FileManagerAware, SettingsAware):  # pylint: disable=too-many-instance-attributes

    def __init__(self, path):
        self.thisdir = None  # Current Working Directory
        self._thisfile = None  # Current File
        self.history = History(self.settings.max_history_size, unique=False)
        self.last_search = None
        self._pointer = 0
        self._pointed_obj = None
        self.pointed_obj = None
        self.path = abspath(expanduser(path))
        self.pathway = ()
        # NOTE: in the line below, weak=True works only in python3.  In python2,
        # weak references are not equal to the original object when tested with
        # "==", and this breaks _set_thisfile_from_signal and _on_tab_change.
        self.fm.signal_bind('move', self._set_thisfile_from_signal,
                            priority=settings.SIGNAL_PRIORITY_AFTER_SYNC,
                            weak=(PY3))
        self.fm.signal_bind('tab.change', self._on_tab_change,
                            weak=(PY3))

    def _set_thisfile_from_signal(self, signal):
        if self == signal.tab:
            self._thisfile = signal.new
            if self == self.fm.thistab:
                self.pointer = self.thisdir.pointer
                self.pointed_obj = self.thisdir.pointed_obj

    def _on_tab_change(self, signal):
        if self == signal.new and self.thisdir:
            # restore the pointer whenever this tab is reopened
            self.thisdir.pointer = self.pointer
            self.thisdir.correct_pointer()

    def _set_thisfile(self, value):
        if value is not self._thisfile:
            previous = self._thisfile
            self.fm.signal_emit('move', previous=previous, new=value, tab=self)

    def _get_thisfile(self):
        return self._thisfile

    thisfile = property(_get_thisfile, _set_thisfile)

    def _get_pointer(self):
        if (
                self.thisdir is not None
                and self.thisdir.files[self._pointer] != self._pointed_obj
        ):
            try:
                self._pointer = self.thisdir.files.index(self._pointed_obj)
            except ValueError:
                self._pointed_obj = self.thisdir.files[self._pointer]
        return self._pointer

    def _set_pointer(self, value):
        self._pointer = value
        self._pointed_obj = self.thisdir.files[self._pointer]

    pointer = property(_get_pointer, _set_pointer)

    def at_level(self, level):
        """Returns the FileSystemObject at the given level.

        level >0 => previews
        level 0 => current file/directory
        level <0 => parent directories
        """
        if level <= 0:
            try:
                return self.pathway[level - 1]
            except IndexError:
                return None
        else:
            directory = self.thisdir
            for _ in range(level):
                if directory is None:
                    return None
                if directory.is_directory:
                    directory = directory.pointed_obj
                else:
                    return None
            return directory

    def get_selection(self):
        if self.thisdir:
            if self.thisdir.marked_items:
                return self.thisdir.get_selection()
            elif self._thisfile:
                return [self._thisfile]
        return []

    def assign_cursor_positions_for_subdirs(self):  # pylint: disable=invalid-name
        """Assign correct cursor positions for subdirectories"""
        last_path = None
        for path in reversed(self.pathway):
            if last_path is None:
                last_path = path
                continue

            path.move_to_obj(last_path)
            last_path = path

    def ensure_correct_pointer(self):
        if self.thisdir:
            self.thisdir.correct_pointer()

    def history_go(self, relative):
        """Move relative in history"""
        if self.history:
            self.history.move(relative).go(history=False)

    def inherit_history(self, other_history):
        self.history.rebase(other_history)

    def enter_dir(self, path, history=True):
        """Enter given path"""
        # TODO: Ensure that there is always a self.thisdir
        if path is None:
            return None
        path = str(path)

        # clear filter in the folder we're leaving
        if self.fm.settings.clear_filters_on_dir_change and self.thisdir:
            self.thisdir.filter = None
            self.thisdir.refilter()

        previous = self.thisdir

        # get the absolute path
        path = normpath(join(self.path, expanduser(path)))
        selectfile = None

        if not isdir(path):
            selectfile = path
            path = dirname(path)
        new_thisdir = self.fm.get_directory(path)

        try:
            os.chdir(path)
        except OSError:
            return True
        self.path = path
        self.thisdir = new_thisdir

        self.thisdir.load_content_if_outdated()

        # build the pathway, a tuple of directory objects which lie
        # on the path to the current directory.
        if path == '/':
            self.pathway = (self.fm.get_directory('/'), )
        else:
            pathway = []
            currentpath = '/'
            for comp in path.split('/'):
                currentpath = join(currentpath, comp)
                pathway.append(self.fm.get_directory(currentpath))
            self.pathway = tuple(pathway)

        self.assign_cursor_positions_for_subdirs()

        # set the current file.
        self.thisdir.sort_directories_first = self.fm.settings.sort_directories_first
        self.thisdir.sort_reverse = self.fm.settings.sort_reverse
        self.thisdir.sort_if_outdated()
        if selectfile:
            self.thisdir.move_to_obj(selectfile)
        if previous and previous.path != path:
            self.thisfile = self.thisdir.pointed_obj
        else:
            # This avoids setting self.pointer (through the 'move' signal) and
            # is required so that you can use enter_dir when switching tabs
            # without messing up the pointer.
            self._thisfile = self.thisdir.pointed_obj

        if history:
            self.history.add(new_thisdir)

        self.fm.signal_emit('cd', previous=previous, new=self.thisdir)

        return True

    def __repr__(self):
        return "<Tab '%s'>" % self.thisdir
