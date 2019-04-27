# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

import re
from grp import getgrgid
from os import lstat, stat
from os.path import abspath, basename, dirname, realpath, relpath, splitext
from pwd import getpwuid
from time import time

from ranger.core.linemode import (
    DEFAULT_LINEMODE, DefaultLinemode, TitleLinemode,
    PermissionsLinemode, FileInfoLinemode, MtimeLinemode, SizeMtimeLinemode,
    HumanReadableMtimeLinemode, SizeHumanReadableMtimeLinemode
)
from ranger.core.shared import FileManagerAware, SettingsAware
from ranger.ext.shell_escape import shell_escape
from ranger.ext import spawn
from ranger.ext.lazy_property import lazy_property
from ranger.ext.human_readable import human_readable

# Python 2 compatibility
try:
    maketrans = str.maketrans  # pylint: disable=invalid-name,no-member
except AttributeError:
    from string import maketrans  # pylint: disable=no-name-in-module


CONTAINER_EXTENSIONS = ('7z', 'ace', 'ar', 'arc', 'bz', 'bz2', 'cab', 'cpio',
                        'cpt', 'deb', 'dgc', 'dmg', 'gz', 'iso', 'jar', 'msi',
                        'pkg', 'rar', 'shar', 'tar', 'tbz', 'tgz', 'txz',
                        'xar', 'xpi', 'xz', 'zip')
DOCUMENT_EXTENSIONS = ('cbr', 'cbz', 'cfg', 'css', 'cvs', 'djvu', 'doc',
                       'docx', 'gnm', 'gnumeric', 'htm', 'html', 'md', 'odf',
                       'odg', 'odp', 'ods', 'odt', 'pdf', 'pod', 'ps', 'rtf',
                       'sxc', 'txt', 'xls', 'xlw', 'xml', 'xslx')
DOCUMENT_BASENAMES = ('bugs', 'bugs', 'changelog', 'copying', 'credits',
                      'hacking', 'help', 'install', 'license', 'readme', 'todo')

BAD_INFO = '?'

_UNSAFE_CHARS = '\n' + ''.join(map(chr, range(32))) + ''.join(map(chr, range(128, 256)))
_SAFE_STRING_TABLE = maketrans(_UNSAFE_CHARS, '?' * len(_UNSAFE_CHARS))
_EXTRACT_NUMBER_RE = re.compile(r'(\d+|\D)')


def safe_path(path):
    return path.translate(_SAFE_STRING_TABLE)


class FileSystemObject(  # pylint: disable=too-many-instance-attributes,too-many-public-methods
        FileManagerAware, SettingsAware):
    basename = None
    relative_path = None
    infostring = None
    path = None
    permissions = None
    stat = None

    content_loaded = False
    force_load = False

    is_device = False
    is_directory = False
    is_file = False
    is_fifo = False
    is_link = False
    is_socket = False

    accessible = False
    exists = False  # "exists" currently means "link_target_exists"
    loaded = False
    marked = False
    runnable = False
    stopped = False
    tagged = False

    audio = False
    container = False
    document = False
    image = False
    media = False
    video = False

    size = 0

    last_load_time = -1

    vcsstatus = None
    vcsremotestatus = None

    linemode_dict = dict(
        (linemode.name, linemode()) for linemode in
        [DefaultLinemode, TitleLinemode, PermissionsLinemode, FileInfoLinemode,
         MtimeLinemode, SizeMtimeLinemode, HumanReadableMtimeLinemode,
         SizeHumanReadableMtimeLinemode]
    )

    def __init__(self, path, preload=None, path_is_abs=False, basename_is_rel_to=None):
        if not path_is_abs:
            path = abspath(path)
        self.path = path
        self.basename = basename(path)
        if basename_is_rel_to is None:
            self.relative_path = self.basename
        else:
            self.relative_path = relpath(path, basename_is_rel_to)
        self.preload = preload
        self.display_data = {}

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self.path)

    @lazy_property
    def extension(self):
        try:
            lastdot = self.basename.rindex('.') + 1
            return self.basename[lastdot:].lower()
        except ValueError:
            return None

    @lazy_property
    def relative_path_lower(self):
        return self.relative_path.lower()

    @lazy_property
    def linemode(self):  # pylint: disable=method-hidden
        # Set the line mode from fm.default_linemodes
        for method, argument, linemode in self.fm.default_linemodes:
            if linemode in self.linemode_dict:
                if method == "always":
                    return linemode
                if method == "path" and argument.search(self.path):
                    return linemode
                if method == "tag" and self.realpath in self.fm.tags and \
                        self.fm.tags.marker(self.realpath) in argument:
                    return linemode
        return DEFAULT_LINEMODE

    @lazy_property
    def dirname(self):
        return dirname(self.path)

    @lazy_property
    def shell_escaped_basename(self):
        return shell_escape(self.basename)

    @lazy_property
    def filetype(self):
        try:
            return spawn.check_output(["file", '-Lb', '--mime-type', self.path])
        except OSError:
            return ""

    @lazy_property
    def basename_natural(self):
        basename_list = []
        for string in _EXTRACT_NUMBER_RE.split(self.relative_path):
            try:
                basename_list += [('0', int(string))]
            except ValueError:
                basename_list += [(string, 0)]
        return basename_list

    @lazy_property
    def basename_natural_lower(self):
        basename_list = []
        for string in _EXTRACT_NUMBER_RE.split(self.relative_path_lower):
            try:
                basename_list += [('0', int(string))]
            except ValueError:
                basename_list += [(string, 0)]
        return basename_list

    @lazy_property
    def basename_without_extension(self):
        return splitext(self.basename)[0]

    @lazy_property
    def safe_basename(self):
        return self.basename.translate(_SAFE_STRING_TABLE)

    @lazy_property
    def user(self):
        try:
            return getpwuid(self.stat.st_uid)[0]
        except KeyError:
            return str(self.stat.st_uid)

    @lazy_property
    def group(self):
        try:
            return getgrgid(self.stat.st_gid)[0]
        except KeyError:
            return str(self.stat.st_gid)

    for attr in ('video', 'audio', 'image', 'media', 'document', 'container'):
        exec(  # pylint: disable=exec-used
            "%s = lazy_property(lambda self: self.set_mimetype() or self.%s)" % (attr, attr))

    def __str__(self):
        """returns a string containing the absolute path"""
        return str(self.path)

    def use(self):
        """Used in garbage-collecting.  Override in Directory"""

    def look_up_cumulative_size(self):
        pass  # normal files have no cumulative size

    def set_mimetype(self):
        """assign attributes such as self.video according to the mimetype"""
        bname = self.basename
        if self.extension == 'part':
            bname = bname[0:-5]
        # pylint: disable=attribute-defined-outside-init
        self._mimetype = self.fm.mimetypes.guess_type(bname, False)[0]
        if self._mimetype is None:
            self._mimetype = ''
        # pylint: enable=attribute-defined-outside-init

        self.video = self._mimetype.startswith('video')
        self.image = self._mimetype.startswith('image')
        self.audio = self._mimetype.startswith('audio')
        self.media = self.video or self.image or self.audio
        self.document = self._mimetype.startswith('text') \
            or self.extension in DOCUMENT_EXTENSIONS \
            or self.basename.lower() in DOCUMENT_BASENAMES
        self.container = self.extension in CONTAINER_EXTENSIONS

        # pylint: disable=attribute-defined-outside-init
        keys = ('video', 'audio', 'image', 'media', 'document', 'container')
        self._mimetype_tuple = tuple(key for key in keys if getattr(self, key))

        if self._mimetype == '':
            self._mimetype = None
        # pylint: enable=attribute-defined-outside-init

    @property
    def mimetype(self):
        try:
            return self._mimetype
        except AttributeError:
            self.set_mimetype()
            return self._mimetype

    @property
    def mimetype_tuple(self):
        try:
            return self._mimetype_tuple
        except AttributeError:
            self.set_mimetype()
            return self._mimetype_tuple

    def mark(self, _):
        directory = self.fm.get_directory(self.dirname)
        directory.mark_item(self)

    def mark_set(self, boolean):
        """Called by directory.mark_item() and similar functions"""
        self.marked = bool(boolean)

    @lazy_property
    def realpath(self):
        if self.is_link:
            try:
                return realpath(self.path)
            except OSError:
                return None  # it is impossible to get the link destination
        return self.path

    def load(self):  # pylint: disable=too-many-statements
        """Loads information about the directory itself.

        reads useful information about the filesystem-object from the
        filesystem and caches it for later use
        """

        self.loaded = True
        if self.settings.freeze_files:
            return

        self.display_data = {}
        self.fm.update_preview(self.path)

        # Get the stat object, either from preload or from [l]stat
        self.permissions = None
        new_stat = None
        path = self.path
        self.is_link = False
        if self.preload:
            new_stat = self.preload[1]
            self.is_link = new_stat.st_mode & 0o170000 == 0o120000
            if self.is_link:
                new_stat = self.preload[0]
            self.preload = None
            self.exists = True if new_stat else False
        else:
            try:
                new_stat = lstat(path)
                self.is_link = new_stat.st_mode & 0o170000 == 0o120000
                if self.is_link:
                    new_stat = stat(path)
                self.exists = True
            except OSError:
                self.exists = False

        # Set some attributes

        self.accessible = True if new_stat else False
        mode = new_stat.st_mode if new_stat else 0

        fmt = mode & 0o170000
        if fmt == 0o020000 or fmt == 0o060000:  # stat.S_IFCHR/BLK
            self.is_device = True
            self.size = 0
            self.infostring = 'dev'
        elif fmt == 0o010000:  # stat.S_IFIFO
            self.is_fifo = True
            self.size = 0
            self.infostring = 'fifo'
        elif fmt == 0o140000:  # stat.S_IFSOCK
            self.is_socket = True
            self.size = 0
            self.infostring = 'sock'
        elif self.is_file:
            if new_stat:
                self.size = new_stat.st_size
                self.infostring = ' ' + human_readable(self.size)
            else:
                self.size = 0
                self.infostring = '?'
        if self.is_link and not self.is_directory:
            self.infostring = '->' + self.infostring

        self.stat = new_stat
        self.last_load_time = time()

    def get_permission_string(self):
        if self.permissions is not None:
            return self.permissions

        if self.is_directory:
            perms = ['d']
        elif self.is_link:
            perms = ['l']
        else:
            perms = ['-']

        mode = self.stat.st_mode
        test = 0o0400
        while test:  # will run 3 times because 0o400 >> 9 = 0
            for what in "rwx":
                if mode & test:
                    perms.append(what)
                else:
                    perms.append('-')
                test >>= 1

        self.permissions = ''.join(perms)
        return self.permissions

    def load_if_outdated(self):
        """Calls load() if the currently cached information is outdated"""
        if not self.loaded:
            self.load()
            return True
        try:
            real_ctime = stat(self.path).st_ctime
        except OSError:
            real_ctime = None
        if not self.stat or self.stat.st_ctime != real_ctime:
            self.load()
            return True
        return False

    def set_linemode(self, mode):
        self.linemode = mode
