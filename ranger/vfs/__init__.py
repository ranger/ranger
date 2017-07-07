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
