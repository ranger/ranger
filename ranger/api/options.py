# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

# THIS WHOLE FILE IS OBSOLETE AND EXISTS FOR BACKWARDS COMPATIBILITIY

from __future__ import (absolute_import, division, print_function)

# pylint: disable=unused-import
import re  # NOQA
from re import compile as regexp  # NOQA

from ranger.api import LinemodeBase, hook_init, hook_ready, register_linemode  # NOQA
from ranger.gui import color  # NOQA
# pylint: enable=unused-import
