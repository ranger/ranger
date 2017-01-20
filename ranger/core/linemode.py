# -*- coding: utf-8 -*-
# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# Author: Wojciech Siewierski <wojciech.siewierski@onet.pl>, 2015

from __future__ import (absolute_import, print_function)

import sys

from abc import ABCMeta, abstractproperty, abstractmethod
from datetime import datetime
from ranger.ext.human_readable import human_readable
from ranger.ext import spawn

DEFAULT_LINEMODE = "filename"


class LinemodeBase(object):
    """Supplies the file line contents for BrowserColumn.

    Attributes:
        name (required!) - Name by which the linemode is referred to by the user

        uses_metadata - True if metadata should to be loaded for this linemode

        required_metadata -
            If any of these metadata fields are absent, fall back to
            the default linemode
    """
    __metaclass__ = ABCMeta

    uses_metadata = False
    required_metadata = []

    name = abstractproperty()

    @abstractmethod
    def filetitle(self, fobj, metadata):
        """The left-aligned part of the line."""
        raise NotImplementedError

    def infostring(self, fobj, metadata):
        """The right-aligned part of the line.

        If `NotImplementedError' is raised (e.g. this method is just
        not implemented in the actual linemode), the caller should
        provide its own implementation (which in this case means
        displaying the hardlink count of the directories, size of the
        files and additionally a symlink marker for symlinks). Useful
        because only the caller (BrowserColumn) possesses the data
        necessary to display that information.

        """
        raise NotImplementedError


class DefaultLinemode(LinemodeBase):  # pylint: disable=abstract-method
    name = "filename"

    def filetitle(self, fobj, metadata):
        return fobj.relative_path


class TitleLinemode(LinemodeBase):
    name = "metatitle"
    uses_metadata = True
    required_metadata = ["title"]

    def filetitle(self, fobj, metadata):
        name = metadata.title
        if metadata.year:
            return "%s - %s" % (metadata.year, name)
        return name

    def infostring(self, fobj, metadata):
        if metadata.authors:
            authorstring = metadata.authors
            if ',' in authorstring:
                authorstring = authorstring[0:authorstring.find(",")]
            return authorstring
        return ""


class PermissionsLinemode(LinemodeBase):
    name = "permissions"

    def filetitle(self, fobj, metadata):
        return "%s %s %s %s" % (
            fobj.get_permission_string(), fobj.user, fobj.group, fobj.relative_path)

    def infostring(self, fobj, metadata):
        return ""


class FileInfoLinemode(LinemodeBase):
    name = "fileinfo"

    def filetitle(self, fobj, metadata):
        return fobj.relative_path

    def infostring(self, fobj, metadata):
        if not fobj.is_directory:
            from subprocess import CalledProcessError
            try:
                fileinfo = spawn.check_output(["file", "-bL", fobj.path]).strip()
            except CalledProcessError:
                return "unknown"
            if sys.version_info[0] >= 3:
                fileinfo = fileinfo.decode("utf-8")
            return fileinfo
        else:
            raise NotImplementedError


class MtimeLinemode(LinemodeBase):
    name = "mtime"

    def filetitle(self, fobj, metadata):
        return fobj.relative_path

    def infostring(self, fobj, metadata):
        return datetime.fromtimestamp(fobj.stat.st_mtime).strftime("%Y-%m-%d %H:%M")


class SizeMtimeLinemode(LinemodeBase):
    name = "sizemtime"

    def filetitle(self, fobj, metadata):
        return fobj.relative_path

    def infostring(self, fobj, metadata):
        return "%s %s" % (human_readable(fobj.size),
                          datetime.fromtimestamp(fobj.stat.st_mtime).strftime("%Y-%m-%d %H:%M"))
