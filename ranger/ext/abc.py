# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import absolute_import

from abc import ABCMeta


# A compat wrapper for the older Python versions.
try:
    from abc import ABC       # pylint: disable=ungrouped-imports,unused-import
except ImportError:
    class ABC(object):        # pylint: disable=too-few-public-methods
        __metaclass__ = ABCMeta
