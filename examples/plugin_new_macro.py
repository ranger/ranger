# Compatible with ranger 1.6.0 through 1.7.*
#
# This plugin adds the new macro %date which is substituted with the current
# date in commands that allow macros.  You can test it with the command
# ":shell echo %date; read"
# Important to note is that the macros can be in the form of functions
# that take no argument. This is done so that the macros can be lazly
# expanded on demand. This is however not necessary if the macro is not
# something callable, its value will be taken and expanded.

from __future__ import (absolute_import, division, print_function)

import time

import ranger.core.actions

# Save the original macro function
GET_MACROS_OLD = ranger.core.actions.Actions.get_macros


# Define a new macro function
def get_macros_with_date(self):
    macros = GET_MACROS_OLD(self)
    macros['date'] = time.strftime('%m/%d/%Y')
    return macros


# Overwrite the old one
ranger.core.actions.Actions.get_macros = get_macros_with_date
