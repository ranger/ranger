# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

# TODO: add a __getitem__ method to get the tag of a file

from __future__ import (absolute_import, division, print_function)

from os.path import isdir, exists, dirname, abspath, realpath, expanduser, sep
import string
import sys

ALLOWED_KEYS = string.ascii_letters + string.digits + string.punctuation


class Tags(object):
    default_tag = '*'

    def __init__(self, filename):

        self._filename = realpath(abspath(expanduser(filename)))

        if isdir(dirname(self._filename)) and not exists(self._filename):
            open(self._filename, 'w')

        self.sync()

    def __contains__(self, item):
        return item in self.tags

    def add(self, *items, **others):
        if 'tag' in others:
            tag = others['tag']
        else:
            tag = self.default_tag
        self.sync()
        for item in items:
            self.tags[item] = tag
        self.dump()

    def remove(self, *items):
        self.sync()
        for item in items:
            try:
                del self.tags[item]
            except KeyError:
                pass
        self.dump()

    def toggle(self, *items, **others):
        if 'tag' in others:
            tag = others['tag']
        else:
            tag = self.default_tag
        tag = str(tag)
        if tag not in ALLOWED_KEYS:
            return
        self.sync()
        for item in items:
            try:
                if item in self and tag in (self.tags[item], self.default_tag):
                    del self.tags[item]
                else:
                    self.tags[item] = tag
            except KeyError:
                pass
        self.dump()

    def marker(self, item):
        if item in self.tags:
            return self.tags[item]
        return self.default_tag

    def sync(self):
        try:
            if sys.version_info[0] >= 3:
                fobj = open(self._filename, 'r', errors='replace')
            else:
                fobj = open(self._filename, 'r')
        except OSError:
            pass
        else:
            self.tags = self._parse(fobj)
            fobj.close()

    def dump(self):
        try:
            fobj = open(self._filename, 'w')
        except OSError:
            pass
        else:
            self._compile(fobj)
            fobj.close()

    def _compile(self, fobj):
        for path, tag in self.tags.items():
            if tag == self.default_tag:
                # COMPAT: keep the old format if the default tag is used
                fobj.write(path + '\n')
            elif tag in ALLOWED_KEYS:
                fobj.write('{0}:{1}\n'.format(tag, path))

    def _parse(self, fobj):
        result = dict()
        for line in fobj:
            line = line.rstrip('\n')
            if len(line) > 2 and line[1] == ':':
                tag, path = line[0], line[2:]
                if tag in ALLOWED_KEYS:
                    result[path] = tag
            else:
                result[line] = self.default_tag

        return result

    def update_path(self, path_old, path_new):
        self.sync()
        changed = False
        for path, tag in self.tags.items():
            pnew = None
            if path == path_old:
                pnew = path_new
            elif path.startswith(path_old + sep):
                pnew = path_new + path[len(path_old):]
            if pnew:
                del self.tags[path]
                self.tags[pnew] = tag
                changed = True
        if changed:
            self.dump()

    def __nonzero__(self):
        return True
    __bool__ = __nonzero__


class TagsDummy(Tags):
    """A dummy Tags class for use with `ranger --clean`.

    It acts like there are no tags and avoids writing any changes.
    """

    def __init__(self, filename):  # pylint: disable=super-init-not-called
        self.tags = dict()

    def __contains__(self, item):
        return False

    def add(self, *items, **others):
        pass

    def remove(self, *items):
        pass

    def toggle(self, *items, **others):
        pass

    def marker(self, item):
        return self.default_tag

    def sync(self):
        pass

    def dump(self):
        pass

    def _compile(self, fobj):
        pass

    def _parse(self, fobj):
        pass
