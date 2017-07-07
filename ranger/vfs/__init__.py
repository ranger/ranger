# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
"""
ranger's Virtual File System module, a FS abstraction layer
"""


class ValueUnusable(object):
    """Base class of enum-like classes to denote unusable metadata"""

class ValueUnknown(ValueUnusable):
    """Denotes values which have not been retrieved yet"""

class ValueInaccessible(ValueUnusable):
    """Denotes values which could not be retrieved"""

class ValueUnhandled(ValueUnusable):
    """Denotes values are valid but not handled by the code"""

class ValueInvalid(ValueUnusable):
    """Denotes values were obtained successfully but seem to be invalid"""

class ValueNotApplicable(ValueUnusable):
    """Denotes that in this particular case, a value would make no sense"""

UNUSABLE = (ValueUnusable, ValueUnknown, ValueInaccessible, ValueUnhandled,
        ValueInvalid, ValueNotApplicable)

class Metadata(object):
    """
    A container for all metadata attributes of a vfs-file

    Every File object will have a Metadata object as an attribute.

    Special care must be taken with Metadata objects, for their properties may
    have "unusable" types which have to be checked for before use.

    I.e. instead of:
        if metadata.st_mtime + 10 < time.time():
    You need to write:
        if metadata.st_mtime not in UNUSABLE and \
                metadata.st_mtime + 10 < time.time():
    Because st_mtime may be ValueNotApplicable, which can not be added.

    Instead of:
        if metadata.link_target_exists:
    You need to write:
        if metadata.link_target_exists == True:
    Because it may be ValueUnknown which would evaluate to True.

    The purpose of this is to represent different states and different results
    of the loading process.  So, always assume that Metadata attributes could
    be unusable and validate them!
    """
    def __init__(self):
        self.refresh()

    def refresh(self):
        self.file_exists = ValueUnknown
        self.filetype = ValueUnknown
        self.is_link = ValueUnknown
        self.link_target_exists = ValueUnknown
        self.path = ValueUnknown
        self.size = ValueUnknown
        self.st_atime = ValueUnknown
        self.st_ctime = ValueUnknown
        self.st_mode = ValueUnknown
        self.st_mtime = ValueUnknown
        self.st_size = ValueUnknown
