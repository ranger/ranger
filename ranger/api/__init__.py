"""
Files in this module contain helper functions used in configuration files.
"""

# Hooks for use in plugins:

def hook_init(fm):
    """
    Parameters:
      fm = the file manager instance
    Return Value:
      ignored

    This hook is executed after fm is initialized but before fm.ui is
    initialized.  You can safely print to stdout and have access to fm to add
    keybindings and such.
    """

def hook_ready(fm):
    """
    Parameters:
      fm = the file manager instance
    Return Value:
      ignored

    This hook is executed after the user interface is initialized.  You should
    NOT print anything to stdout anymore from here on.  Use fm.notify instead.
    """
