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

    def infostring(self, file, metadata):
        """The right-aligned part of the line.

        If `NotImplementedError' is raised (e.g. this method is just
        not implemented in the actual linemode), the caller should
        provide its own implementation, which in this case means
        displaying the hardlink count of the directories. Useful
        because only the caller (BrowserColumn) possesses the data
        necessary to display that information.

        """
        raise NotImplementedError


class DefaultLinemode(LinemodeBase):
    name = "filename"

    def filetitle(self, file, metadata):
        return file.relative_path


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
                file.user, file.group, file.relative_path)

    def infostring(self, file, metadata):
        return ""
