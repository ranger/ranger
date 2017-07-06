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

UNUSABLE = (ValueUnusable, ValueUnknown, ValueInaccessible, ValueUnhandled, ValueInvalid)

class Metadata(object):
    def __init__(self):
        self.refresh()

    def refresh(self):
        self.filetype = ValueUnknown
        self.permission_mode = ValueUnknown
        self.path = ValueUnknown
