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

def register_linemode(*linemodes):
    """Register the linemodes in a dictionary of the available linemodes."""
    from ranger.container.fsobject import FileSystemObject
    for linemode in linemodes:
        FileSystemObject.linemode_dict[linemode.name] = linemode()

def chdir_hook(fun):
    """A decorator used to register a chdir hook.

    Two arguments will be passed to the hook: the previous cwd and the
    new cwd. If the hook returns True, the rest of the hooks will not
    be run.

    The hooks are called already from the new cwd.

    This decorator appends the new hook at the end of the hook list.

    """
    from ranger.core.tab import Tab
    Tab.after_chdir_hooks.append(fun)
    return fun
