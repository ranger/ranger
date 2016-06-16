# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

# TODO: add a __getitem__ method to get the tag of a file

from os.path import isdir, exists, dirname, abspath, realpath, expanduser
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
                del(self.tags[item])
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
                    del(self.tags[item])
                else:
                    self.tags[item] = tag
            except KeyError:
                pass
        self.dump()

    def marker(self, item):
        if item in self.tags:
            return self.tags[item]
        else:
            return self.default_tag

    def sync(self):
        try:
            if sys.version_info[0] >= 3:
                f = open(self._filename, 'r', errors='replace')
            else:
                f = open(self._filename, 'r')
        except OSError:
            pass
        else:
            self.tags = self._parse(f)
            f.close()

    def dump(self):
        try:
            f = open(self._filename, 'w')
        except OSError:
            pass
        else:
            self._compile(f)
            f.close()

    def _compile(self, f):
        for path, tag in self.tags.items():
            if tag == self.default_tag:
                # COMPAT: keep the old format if the default tag is used
                f.write(path + '\n')
            elif tag in ALLOWED_KEYS:
                f.write('{0}:{1}\n'.format(tag, path))

    def _parse(self, f):
        result = dict()
        for line in f:
            line = line.strip()
            if len(line) > 2 and line[1] == ':':
                tag, path = line[0], line[2:]
                if tag in ALLOWED_KEYS:
                    result[path] = tag
            else:
                result[line] = self.default_tag

        return result

    def __nonzero__(self):
        return True
    __bool__ = __nonzero__


class TagsDummy(Tags):
    """A dummy Tags class for use with `ranger --clean`.

    It acts like there are no tags and avoids writing any changes.
    """

    def __init__(self, filename):
        self.tags = dict()

    def __contains__(self, item):
        return False

    def add(self, *items, **others):
        pass

    def remove(self, *items, **others):
        pass

    def toggle(self, *items, **others):
        pass

    def marker(self, item):
        return self.default_tag

    def sync(self):
        pass

    def dump(self):
        pass

    def _compile(self, f):
        pass

    def _parse(self, f):
        pass
