# ===================================================================
# This is the main configuration file of ranger.  It consists of python code,
# but fear not, you don't need any python knowledge for this.
#
# Lines beginning with # are comments.  To enable a line, remove the #.
#
# Technical information:  This file is imported as a python module.  Every
# top-level variable with the name of a ranger setting will be used to change
# the value of that setting.  You can use "del <variable-name>" to avoid that.
# ===================================================================

# This line imports some basic variables to get some basic variables
from ranger.api.options import *

# T
#column_ratios = (1, 1, 4, 3)

# A function that adds an additional macro:
#
## Save the original macro function
#import ranger.actions
#old_get_macros = ranger.actions.Actions.get_macros
#
## Define a new macro function
#import time
#def add_my_macro(self):
#  macros = old_get_macros(self)
#  macros['date'] = time.strftime('%m/%d/%Y')
#  return macros
#
## Overwrite the old one
#ranger.actions.Actions.get_macros = add_my_macro
