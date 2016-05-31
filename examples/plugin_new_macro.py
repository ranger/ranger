# Compatible with ranger 1.6.0 through 1.7.*
#
# This plugin adds the new macro %date which is substituted with the current
# date in commands that allow macros.  You can test it with the command
# ":shell echo %date; read"

# Save the original macro function
import ranger.core.actions
old_get_macros = ranger.core.actions.Actions._get_macros

# Define a new macro function
import time
def get_macros_with_date(self):
    macros = old_get_macros(self)
    macros['date'] = time.strftime('%m/%d/%Y')
    return macros

# Overwrite the old one
ranger.core.actions.Actions._get_macros = get_macros_with_date
