# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

import locale
import os.path
from os import stat as os_stat, lstat as os_lstat
import random
import re
from collections import deque
from time import time

from ranger.container.fsobject import BAD_INFO, FileSystemObject
from ranger.core.loader import Loadable
from ranger.ext.mount_path import mount_path
from ranger.container.file import File
from ranger.ext.accumulator import Accumulator
from ranger.ext.lazy_property import lazy_property
from ranger.ext.human_readable import human_readable
from ranger.container.settings import LocalSettings
from ranger.ext.vcs import Vcs


def sort_by_basename(path):
    """returns path.relative_path (for sorting)"""
    return path.relative_path


def sort_by_basename_icase(path):
    """returns case-insensitive path.relative_path (for sorting)"""
    return path.relative_path_lower


def sort_by_directory(path):
    """returns 0 if path is a directory, otherwise 1 (for sorting)"""
    return 1 - path.is_directory


def sort_naturally(path):
    return path.basename_natural


def sort_naturally_icase(path):
    return path.basename_natural_lower


def sort_unicode_wrapper_string(old_sort_func):
    def sort_unicode(path):
        return locale.strxfrm(old_sort_func(path))
    return sort_unicode


def sort_unicode_wrapper_list(old_sort_func):
    def sort_unicode(path):
        return [locale.strxfrm(str(c)) for c in old_sort_func(path)]
    return sort_unicode


def accept_file(fobj, filters):
    """
    Returns True if file shall be shown, otherwise False.
    Parameters:
        fobj - an instance of FileSystemObject
        filters - an array of lambdas, each expects a fobj and
                  returns True if fobj shall be shown,
                  otherwise False.
    """
    for filt in filters:
        if filt and not filt(fobj):
            return False
    return True


def walklevel(some_dir, level):
    some_dir = some_dir.rstrip(os.path.sep)
    followlinks = True if level > 0 else False
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir, followlinks=followlinks):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if level != -1 and num_sep + level <= num_sep_this:
            del dirs[:]


def mtimelevel(path, level):
    mtime = os.stat(path).st_mtime
    for dirpath, dirnames, _ in walklevel(path, level):
        dirlist = [os.path.join("/", dirpath, d) for d in dirnames
                   if level == -1 or dirpath.count(os.path.sep) - path.count(os.path.sep) <= level]
        mtime = max(mtime, max([-1] + [os.stat(d).st_mtime for d in dirlist]))
    return mtime


class InodeFilterConstants(object):  # pylint: disable=too-few-public-methods
    DIRS = 'd'
    FILES = 'f'
    LINKS = 'l'


class Directory(  # pylint: disable=too-many-instance-attributes,too-many-public-methods
        FileSystemObject, Accumulator, Loadable):
    is_directory = True
    enterable = False
    load_generator = None
    cycle_list = None
    loading = False
    progressbar_supported = True
    flat = 0

    filenames = None
    files = None
    files_all = None
    filter = None
    temporary_filter = None
    narrow_filter = None
    inode_type_filter = None
    marked_items = None
    scroll_begin = 0

    mount_path = '/'
    disk_usage = 0

    last_update_time = -1
    load_content_mtime = -1

    order_outdated = False
    content_outdated = False
    content_loaded = False

    has_vcschild = False
    _vcs_signal_handler_installed = False

    cumulative_size_calculated = False

    sort_dict = {
        'basename': sort_by_basename,
        'natural': sort_naturally,
        'size': lambda path: -(path.size or 1),
        'mtime': lambda path: -(path.stat and path.stat.st_mtime or 1),
        'ctime': lambda path: -(path.stat and path.stat.st_ctime or 1),
        'atime': lambda path: -(path.stat and path.stat.st_atime or 1),
        'random': lambda path: random.random(),
        'type': lambda path: path.mimetype or '',
        'extension': lambda path: path.extension or '',
    }

    def __init__(self, path, **kw):
        assert not os.path.isfile(path), "No directory given!"

        Loadable.__init__(self, None, None)
        Accumulator.__init__(self)
        FileSystemObject.__init__(self, path, **kw)

        self.marked_items = []

        self._signal_functions = []
        func = self.signal_function_factory(self.sort)
        self._signal_functions += [func]
        for opt in ('sort_directories_first', 'sort', 'sort_reverse', 'sort_case_insensitive'):
            self.settings.signal_bind('setopt.' + opt, func, weak=True, autosort=False)
        func = self.signal_function_factory(self.refilter)
        self._signal_functions += [func]
        for opt in ('hidden_filter', 'show_hidden'):
            self.settings.signal_bind('setopt.' + opt, func, weak=True, autosort=False)

        self.settings = LocalSettings(path, self.settings)

        self.use()

    @lazy_property
    def vcs(self):
        if not self._vcs_signal_handler_installed:
            self.settings.signal_bind(
                'setopt.vcs_aware', self.vcs__reset,  # pylint: disable=no-member
                weak=True, autosort=False,
            )
            self._vcs_signal_handler_installed = True
        if self.settings.vcs_aware:
            return Vcs(self)
        return None

    def signal_function_factory(self, function):
        def signal_function():
            self.load_if_outdated()
            if not self.exists:
                return
            function()
        return signal_function

    def request_resort(self):
        self.order_outdated = True

    def request_reload(self):
        self.content_outdated = True

    def get_list(self):
        return self.files

    def mark_item(self, item, val):
        item.mark_set(val)
        if val:
            if item in self.files and item not in self.marked_items:
                self.marked_items.append(item)
        else:
            while True:
                try:
                    self.marked_items.remove(item)
                except ValueError:
                    break

    def toggle_mark(self, item):
        self.mark_item(item, not item.marked)

    def toggle_all_marks(self):
        for item in self.files:
            self.toggle_mark(item)

    def mark_all(self, val):
        for item in self.files:
            self.mark_item(item, val)

        if not val:
            del self.marked_items[:]
            self._clear_marked_items()

    # XXX: Is it really necessary to have the marked items in a list?
    # Can't we just recalculate them with [f for f in self.files if f.marked]?
    def _gc_marked_items(self):
        for item in list(self.marked_items):
            if item.path not in self.filenames:
                self.marked_items.remove(item)

    def _clear_marked_items(self):
        for item in self.marked_items:
            item.mark_set(False)
        del self.marked_items[:]

    def get_selection(self):
        """READ ONLY"""
        self._gc_marked_items()
        if not self.files:
            return []

        if self.marked_items:
            return [item for item in self.files if item.marked]
        elif self.pointed_obj:
            return [self.pointed_obj]

        return []

    def refilter(self):
        if self.files_all is None:
            return  # propably not loaded yet

        self.last_update_time = time()

        filters = []

        if not self.settings.show_hidden and self.settings.hidden_filter:
            hidden_filter = re.compile(self.settings.hidden_filter)
            hidden_filter_search = hidden_filter.search

            def hidden_filter_func(fobj):
                for comp in fobj.relative_path.split(os.path.sep):
                    if hidden_filter_search(comp):
                        return False
                return True
            filters.append(hidden_filter_func)
        if self.narrow_filter:
            # pylint: disable=unsupported-membership-test

            # Pylint complains that self.narrow_filter is by default
            # None but the execution won't reach this line if it is
            # still None.
            filters.append(lambda fobj: fobj.basename in self.narrow_filter)
        if self.settings.global_inode_type_filter or self.inode_type_filter:
            def inode_filter_func(obj):
                # Use local inode_type_filter if present, global otherwise
                inode_filter = self.inode_type_filter or self.settings.global_inode_type_filter
                # Apply filter
                if InodeFilterConstants.DIRS in inode_filter and \
                        obj.is_directory:
                    return True
                elif InodeFilterConstants.FILES in inode_filter and \
                        obj.is_file and not obj.is_link:
                    return True
                elif InodeFilterConstants.LINKS in inode_filter and \
                        obj.is_link:
                    return True
                return False
            filters.append(inode_filter_func)
        if self.filter:
            filter_search = self.filter.search
            filters.append(lambda fobj: filter_search(fobj.basename))
        if self.temporary_filter:
            temporary_filter_search = self.temporary_filter.search
            filters.append(lambda fobj: temporary_filter_search(fobj.basename))

        self.files = [f for f in self.files_all if accept_file(f, filters)]

        # A fix for corner cases when the user invokes show_hidden on a
        # directory that contains only hidden directories and hidden files.
        if self.files and not self.pointed_obj:
            self.pointed_obj = self.files[0]
        elif not self.files:
            self.content_loaded = False
            self.pointed_obj = None

        self.move_to_obj(self.pointed_obj)

    # XXX: Check for possible race conditions
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    def load_bit_by_bit(self):
        """An iterator that loads a part on every next() call

        Returns a generator which load a part of the directory
        in each iteration.
        """

        self.loading = True
        self.percent = 0
        self.load_if_outdated()

        basename_is_rel_to = self.path if self.flat else None

        try:  # pylint: disable=too-many-nested-blocks
            if self.runnable:
                yield
                mypath = self.path

                self.mount_path = mount_path(mypath)

                if self.flat:
                    filelist = []
                    for dirpath, dirnames, filenames in walklevel(mypath, self.flat):
                        dirlist = [
                            os.path.join("/", dirpath, d)
                            for d in dirnames
                            if self.flat == -1
                            or (dirpath.count(os.path.sep)
                                - mypath.count(os.path.sep)) <= self.flat
                        ]
                        filelist += dirlist
                        filelist += [os.path.join("/", dirpath, f) for f in filenames]
                    filenames = filelist
                    self.load_content_mtime = mtimelevel(mypath, self.flat)
                else:
                    filelist = os.listdir(mypath)
                    filenames = [mypath + (mypath == '/' and fname or '/' + fname)
                                 for fname in filelist]
                    self.load_content_mtime = os.stat(mypath).st_mtime

                if self.cumulative_size_calculated:
                    # If self.content_loaded is true, this is not the first
                    # time loading.  So I can't really be sure if the
                    # size has changed and I'll add a "?".
                    if self.content_loaded:
                        if self.fm.settings.autoupdate_cumulative_size:
                            self.look_up_cumulative_size()
                        else:
                            self.infostring = ' %s' % human_readable(
                                self.size, separator='? ')
                    else:
                        self.infostring = ' %s' % human_readable(self.size)
                else:
                    self.size = len(filelist)
                    self.infostring = ' %d' % self.size
                if self.is_link:
                    self.infostring = '->' + self.infostring

                yield

                marked_paths = [obj.path for obj in self.marked_items]

                files = []
                disk_usage = 0

                has_vcschild = False
                for name in filenames:
                    try:
                        file_lstat = os_lstat(name)
                        if file_lstat.st_mode & 0o170000 == 0o120000:
                            file_stat = os_stat(name)
                        else:
                            file_stat = file_lstat
                    except OSError:
                        file_lstat = None
                        file_stat = None
                    if file_lstat and file_stat:
                        stats = (file_stat, file_lstat)
                        is_a_dir = file_stat.st_mode & 0o170000 == 0o040000
                    else:
                        stats = None
                        is_a_dir = False

                    if is_a_dir:
                        item = self.fm.get_directory(name, preload=stats, path_is_abs=True,
                                                     basename_is_rel_to=basename_is_rel_to)
                        item.load_if_outdated()
                        if self.flat:
                            item.relative_path = os.path.relpath(item.path, self.path)
                        else:
                            item.relative_path = item.basename
                        item.relative_path_lower = item.relative_path.lower()
                        if item.vcs and item.vcs.track:
                            if item.vcs.is_root_pointer:
                                has_vcschild = True
                            else:
                                item.vcsstatus = \
                                    item.vcs.rootvcs.status_subpath(  # pylint: disable=no-member
                                        os.path.join(self.realpath, item.basename),
                                        is_directory=True,
                                    )
                    else:
                        item = File(name, preload=stats, path_is_abs=True,
                                    basename_is_rel_to=basename_is_rel_to)
                        item.load()
                        disk_usage += item.size
                        if self.vcs and self.vcs.track:
                            item.vcsstatus = \
                                self.vcs.rootvcs.status_subpath(  # pylint: disable=no-member
                                    os.path.join(self.realpath, item.basename))

                    files.append(item)
                    self.percent = 100 * len(files) // len(filenames)
                    yield
                self.has_vcschild = has_vcschild
                self.disk_usage = disk_usage

                self.filenames = filenames
                self.files_all = files

                self._clear_marked_items()
                for item in self.files_all:
                    if item.path in marked_paths:
                        item.mark_set(True)
                        self.marked_items.append(item)
                    else:
                        item.mark_set(False)

                self.sort()

                if files:
                    if self.pointed_obj is not None:
                        self.sync_index()
                    else:
                        self.move(to=0)
            else:
                self.filenames = None
                self.files_all = None
                self.files = None

            self.cycle_list = None
            self.content_loaded = True
            self.last_update_time = time()
            self.correct_pointer()

        finally:
            self.loading = False
            self.fm.signal_emit("finished_loading_dir", directory=self)
            if self.vcs:
                self.fm.ui.vcsthread.process(self)
    # pylint: enable=too-many-locals,too-many-branches,too-many-statements

    def unload(self):
        self.loading = False
        self.load_generator = None

    def load_content(self, schedule=None):
        """Loads the contents of the directory.

        Use this sparingly since it takes rather long.
        """
        self.content_outdated = False
        if self.settings.freeze_files:
            return

        if not self.loading:
            if not self.loaded:
                self.load()

            if not self.accessible:
                self.content_loaded = True
                return

            if schedule is None:
                schedule = True   # was: self.size > 30

            if self.load_generator is None:
                self.load_generator = self.load_bit_by_bit()

                if schedule and self.fm:
                    self.fm.loader.add(self)
                else:
                    for _ in self.load_generator:
                        pass
                    self.load_generator = None

            elif not schedule or not self.fm:
                for _ in self.load_generator:
                    pass
                self.load_generator = None

    def sort(self):
        """Sort the contained files"""
        if self.files_all is None:
            return

        try:
            sort_func = self.sort_dict[self.settings.sort]
        except KeyError:
            sort_func = sort_by_basename

        if self.settings.sort_case_insensitive and \
                sort_func == sort_by_basename:
            sort_func = sort_by_basename_icase

        if self.settings.sort_case_insensitive and \
                sort_func == sort_naturally:
            sort_func = sort_naturally_icase

        # XXX Does not work with usermade sorting functions :S
        if self.settings.sort_unicode:
            if sort_func in (sort_naturally, sort_naturally_icase):
                sort_func = sort_unicode_wrapper_list(sort_func)
            elif sort_func in (sort_by_basename, sort_by_basename_icase):
                sort_func = sort_unicode_wrapper_string(sort_func)

        self.files_all.sort(key=sort_func)

        if self.settings.sort_reverse:
            self.files_all.reverse()

        if self.settings.sort_directories_first:
            self.files_all.sort(key=sort_by_directory)

        self.refilter()

    def _get_cumulative_size(self):
        if self.size == 0:
            return 0
        cum = 0
        realpath = os.path.realpath
        for dirpath, _, filenames in os.walk(self.path, onerror=lambda _: None):
            for fname in filenames:
                try:
                    if dirpath == self.path:
                        stat = os_stat(realpath(dirpath + "/" + fname))
                    else:
                        stat = os_stat(dirpath + "/" + fname)
                except OSError:
                    continue
                cum += stat.st_size
        return cum

    def look_up_cumulative_size(self):
        self.cumulative_size_calculated = True
        self.size = self._get_cumulative_size()
        self.infostring = ('-> ' if self.is_link else ' ') + human_readable(self.size)

    @lazy_property
    def size(self):  # pylint: disable=method-hidden
        try:
            if self.fm.settings.automatically_count_files:
                size = len(os.listdir(self.path))
            else:
                size = None
        except OSError:
            self.infostring = BAD_INFO
            self.accessible = False
            self.runnable = False
            return 0
        else:
            if size is None:
                self.infostring = ''
            else:
                self.infostring = ' %d' % size
            self.accessible = True
            self.runnable = True
            return size

    @lazy_property
    def infostring(self):  # pylint: disable=method-hidden
        self.size  # trigger the lazy property initializer pylint: disable=pointless-statement
        if self.is_link:
            return '->' + self.infostring
        return self.infostring

    @lazy_property
    def runnable(self):  # pylint: disable=method-hidden
        self.size  # trigger the lazy property initializer pylint: disable=pointless-statement
        return self.runnable

    def sort_if_outdated(self):
        """Sort the containing files if they are outdated"""
        if self.order_outdated:
            self.order_outdated = False
            self.sort()
            return True
        return False

    def move_to_obj(self, arg, attr=None):
        try:
            arg = arg.path
        except AttributeError:
            pass
        self.load_content_once(schedule=False)
        if self.empty():
            return

        Accumulator.move_to_obj(self, arg, attr='path')

    def search_fnc(self, fnc, offset=1, forward=True):
        length = len(self)
        if forward:
            generator = ((self.pointer + (x + offset)) % length
                         for x in range(length - 1))
        else:
            generator = ((self.pointer - (x + offset)) % length
                         for x in range(length - 1))

        for i in generator:
            _file = self.files[i]
            if fnc(_file):
                self.pointer = i
                self.pointed_obj = _file
                self.correct_pointer()
                return True
        return False

    def set_cycle_list(self, lst):
        self.cycle_list = deque(lst)

    def cycle(self, forward=True):
        if self.cycle_list:
            if forward is True:
                self.cycle_list.rotate(-1)
            elif forward is False:
                self.cycle_list.rotate(1)

            self.move_to_obj(self.cycle_list[0])

    def correct_pointer(self):
        """Make sure the pointer is in the valid range"""
        Accumulator.correct_pointer(self)

        if self == self.fm.thisdir:
            try:
                self.fm.thisfile = self.pointed_obj
            except AttributeError:
                pass

    def load_content_once(self, *a, **k):
        """Load the contents of the directory if not done yet"""
        if not self.content_loaded:
            self.load_content(*a, **k)
            return True
        return False

    def load_content_if_outdated(self, *a, **k):
        """Load the contents of the directory if outdated"""

        if self.load_content_once(*a, **k):
            return True

        if self.files_all is None or self.content_outdated:
            self.load_content(*a, **k)
            return True

        try:
            if self.flat:
                real_mtime = mtimelevel(self.path, self.flat)
            else:
                real_mtime = os.stat(self.path).st_mtime
        except OSError:
            real_mtime = None
            return False
        if self.stat:
            cached_mtime = self.load_content_mtime
        else:
            cached_mtime = 0

        if real_mtime != cached_mtime:
            self.load_content(*a, **k)
            return True
        return False

    def get_description(self):
        return "Loading " + str(self)

    def use(self):
        """mark the filesystem-object as used at the current time"""
        self.last_used = time()

    def is_older_than(self, seconds):
        """returns whether this object wasn't use()d in the last n seconds"""
        if seconds < 0:
            return True
        return self.last_used + seconds < time()

    def go(self, history=True):  # pylint: disable=invalid-name
        """enter the directory if the filemanager is running"""
        if self.fm:
            return self.fm.enter_dir(self.path, history=history)
        return False

    def empty(self):
        """Is the directory empty?"""
        return not self.files

    def set_linemode_of_children(self, mode):
        for fobj in self.files:
            fobj.set_linemode(mode)

    def __nonzero__(self):
        """Always True"""
        return True
    __bool__ = __nonzero__

    def __len__(self):
        """The number of containing files"""
        assert self.accessible
        assert self.content_loaded
        assert self.files is not None
        return len(self.files)

    def __eq__(self, other):
        """Check for equality of the directories paths"""
        return isinstance(other, Directory) and self.path == other.path

    def __neq__(self, other):
        """Check for inequality of the directories paths"""
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.path)
