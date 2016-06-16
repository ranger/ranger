# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""Files in this module contain helper functions used in configuration files."""

# Hooks for use in plugins:


def hook_init(fm):
    """A hook that is called when ranger starts up.

    Parameters:
      fm = the file manager instance
    Return Value:
      ignored

    This hook is executed after fm is initialized but before fm.ui is
    initialized.  You can safely print to stdout and have access to fm to add
    keybindings and such.
    """


def hook_ready(fm):
    """A hook that is called after the ranger UI is initialized.

    Parameters:
      fm = the file manager instance
    Return Value:
      ignored

    This hook is executed after the user interface is initialized.  You should
    NOT print anything to stdout anymore from here on.  Use fm.notify instead.
    """

from ranger.core.linemode import LinemodeBase


def register_linemode(linemode_class):
    """Add a custom linemode class.  See ranger.core.linemode"""
    from ranger.container.fsobject import FileSystemObject
    FileSystemObject.linemode_dict[linemode_class.name] = linemode_class()
    return linemode_class
