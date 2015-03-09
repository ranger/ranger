# -*- coding: utf-8 -*-

from abc import *

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
    def filetitle(self, file, metadata):
        """The left-aligned part of the line."""
        raise NotImplementedError

    @abstractmethod
    def infostring(self, file, metadata):
        """The right-aligned part of the line."""
        raise NotImplementedError


class DefaultLinemode(LinemodeBase):
    name = "filename"

    def filetitle(self, file, metadata):
        return file.drawn_basename

    def infostring(self, file, metadata):
        # Should never be called for this linemode, implemented in BrowserColumn
        raise NotImplementedError


class TitleLinemode(LinemodeBase):
    name = "metatitle"
    uses_metadata = True
    required_metadata = ["title"]

    def filetitle(self, file, metadata):
        name = metadata.title or file.basename
        if metadata.year:
            return "%s - %s" % (metadata.year, name)
        else:
            return name

    def infostring(self, file, metadata):
        if metadata.authors:
            authorstring = metadata.authors
            if ',' in authorstring:
                authorstring = authorstring[0:authorstring.find(",")]
            return authorstring
        return ""


class PermissionsLinemode(LinemodeBase):
    name = "permissions"

    def filetitle(self, file, metadata):
        return "%s %s %s %s" % (file.get_permission_string(),
                file.user, file.group, file.drawn_basename)

    def infostring(self, file, metadata):
        return ""
