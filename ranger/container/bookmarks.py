# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

import string
import re
import os

from ranger.core.shared import FileManagerAware

ALLOWED_KEYS = string.ascii_letters + string.digits + "`'"


class Bookmarks(FileManagerAware):
    """Bookmarks is a container which associates keys with bookmarks.

    A key is a string with: len(key) == 1 and key in ALLOWED_KEYS.

    A bookmark is an object with: bookmark == bookmarktype(str(instance))
    Which is true for str or FileSystemObject. This condition is required
    so bookmark-objects can be saved to and loaded from a file.

    Optionally, a bookmark.go() method is used for entering a bookmark.
    """

    last_mtime = None
    autosave = True
    load_pattern = re.compile(r"^[\d\w']:.")

    def __init__(self, bookmarkfile, bookmarktype=str, autosave=False,
                 nonpersistent_bookmarks=()):
        """Initializes Bookmarks.

        <bookmarkfile> specifies the path to the file where
        bookmarks are saved in.
        """
        self.autosave = autosave
        self.dct = {}
        self.original_dict = {}
        self.path = bookmarkfile
        self.bookmarktype = bookmarktype
        self.nonpersistent_bookmarks = set(nonpersistent_bookmarks)

    def load(self):
        """Load the bookmarks from path/bookmarks"""
        new_dict = self._load_dict()
        if new_dict is None:
            return

        self._set_dict(new_dict, original=new_dict)

    def enter(self, key):
        """Enter the bookmark with the given key.

        Requires the bookmark instance to have a go() method.
        """

        try:
            return self[key].go()
        except (IndexError, KeyError, AttributeError):
            return False

    def update_if_outdated(self):
        if self.last_mtime != self._get_mtime():
            self.update()

    def remember(self, value):
        """Bookmarks <value> to the key '"""
        self["'"] = value
        if self.autosave:
            self.save()

    def __delitem__(self, key):
        """Delete the bookmark with the given key"""
        if key == '`':
            key = "'"
        if key in self.dct:
            del self.dct[key]
            if self.autosave:
                self.save()

    def __iter__(self):
        return iter(self.dct.items())

    def __getitem__(self, key):
        """Get the bookmark associated with the key"""
        if key == '`':
            key = "'"
        if key in self.dct:
            return self.dct[key]
        else:
            raise KeyError("Nonexistant Bookmark: `%s'!" % key)

    def __setitem__(self, key, value):
        """Bookmark <value> to the key <key>.

        key is expected to be a 1-character string and element of ALLOWED_KEYS.
        value is expected to be a filesystemobject.
        """
        if key == '`':
            key = "'"
        if key in ALLOWED_KEYS:
            self.dct[key] = value
            if self.autosave:
                self.save()

    def __contains__(self, key):
        """Test whether a bookmark-key is defined"""
        return key in self.dct

    def update_path(self, path_old, file_new):
        """Update bookmarks containing path"""
        self.update_if_outdated()
        changed = False
        for key, bfile in self:
            if bfile.path == path_old:
                self.dct[key] = file_new
                changed = True
            elif bfile.path.startswith(path_old + os.path.sep):
                self.dct[key] = self.bookmarktype(file_new.path + bfile.path[len(path_old):])
                changed = True
        if changed:
            self.save()

    def update(self):
        """Update the bookmarks from the bookmark file.

        Useful if two instances are running which define different bookmarks.
        """
        real_dict = self._load_dict()
        if real_dict is None:
            return
        real_dict_copy = real_dict.copy()

        for key in set(self.dct) | set(real_dict):
            # set some variables
            if key in self.dct:
                current = self.dct[key]
            else:
                current = None

            if key in self.original_dict:
                original = self.original_dict[key]
            else:
                original = None

            if key in real_dict:
                real = real_dict[key]
            else:
                real = None

            # determine if there have been changes
            if current == original and current != real:
                continue   # another ranger instance has changed the bookmark

            if key not in self.dct:
                del real_dict[key]   # the user has deleted it
            else:
                real_dict[key] = current   # the user has changed it

        self._set_dict(real_dict, original=real_dict_copy)

    def save(self):
        """Save the bookmarks to the bookmarkfile.

        This is done automatically after every modification if autosave is True."""
        self.update()
        if self.path is None:
            return

        path_new = self.path + '.new'
        try:
            fobj = open(path_new, 'w')
        except OSError as ex:
            self.fm.notify('Bookmarks error: {0}'.format(str(ex)), bad=True)
            return
        for key, value in self.dct.items():
            if isinstance(key, str) and key in ALLOWED_KEYS \
                    and key not in self.nonpersistent_bookmarks:
                fobj.write("{0}:{1}\n".format(str(key), str(value)))
        fobj.close()

        try:
            old_perms = os.stat(self.path)
            os.chown(path_new, old_perms.st_uid, old_perms.st_gid)
            os.chmod(path_new, old_perms.st_mode)
            os.rename(path_new, self.path)
        except OSError as ex:
            self.fm.notify('Bookmarks error: {0}'.format(str(ex)), bad=True)
            return

        self._update_mtime()

    def enable_saving_backtick_bookmark(self, boolean):
        """
        Adds or removes the ' from the list of nonpersitent bookmarks
        """
        if boolean:
            if "'" in self.nonpersistent_bookmarks:
                self.nonpersistent_bookmarks.remove("'")  # enable
        else:
            self.nonpersistent_bookmarks.add("'")  # disable

    def _load_dict(self):
        if self.path is None:
            return {}

        if not os.path.exists(self.path):
            try:
                with open(self.path, 'w') as fobj:
                    pass
            except OSError as ex:
                self.fm.notify('Bookmarks error: {0}'.format(str(ex)), bad=True)
                return None

        try:
            fobj = open(self.path, 'r')
        except OSError as ex:
            self.fm.notify('Bookmarks error: {0}'.format(str(ex)), bad=True)
            return None
        dct = {}
        for line in fobj:
            if self.load_pattern.match(line):
                key, value = line[0], line[2:-1]
                if key in ALLOWED_KEYS and not os.path.isfile(value):
                    dct[key] = self.bookmarktype(value)
        fobj.close()
        return dct

    def _set_dict(self, dct, original):
        if original is None:
            original = {}

        self.dct.clear()
        self.dct.update(dct)
        self.original_dict = original
        self._update_mtime()

    def _get_mtime(self):
        if self.path is None:
            return None
        try:
            return os.stat(self.path).st_mtime
        except OSError:
            return None

    def _update_mtime(self):
        self.last_mtime = self._get_mtime()
