# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""Files in this module contain helper functions used in configuration files."""

from __future__ import (absolute_import, division, print_function)

import ranger
from ranger.core.linemode import LinemodeBase


__all__ = ['ranger', 'LinemodeBase', 'hook_init', 'hook_ready', 'register_linemode']


# Hooks for use in plugins:
def hook_init(fm):  # pylint: disable=unused-argument
    """A hook that is called when ranger starts up.

    Parameters:
      fm = the file manager instance
    Return Value:
      ignored

    This hook is executed after fm is initialized but before fm.ui is
    initialized.  You can safely print to stdout and have access to fm to add
    keybindings and such.
    """


def hook_ready(fm):  # pylint: disable=unused-argument
    """A hook that is called after the ranger UI is initialized.

    Parameters:
      fm = the file manager instance
    Return Value:
      ignored

    This hook is executed after the user interface is initialized.  You should
    NOT print anything to stdout anymore from here on.  Use fm.notify instead.
    """


def register_linemode(linemode_class):
    """Add a custom linemode class.  See ranger.core.linemode"""
    from ranger.container.fsobject import FileSystemObject
    FileSystemObject.linemode_dict[linemode_class.name] = linemode_class()
    return linemode_class
