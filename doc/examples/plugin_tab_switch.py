# Compatible since ranger 1.6.1
#
# This plugin adds a new action, tab_switch, which switches to a tab of
# the specified directory, opening a new tab if necessary.  An option
# is provided to create the directory if it does not exist.

import ranger.api
import os

old_hook_ready = ranger.api.hook_ready

def tab_switch(self, path, create_directory=True):
    """Switches to tab of given path, opening a new tab as necessary.

    If path does not exist, it is treated as a directory.
    """
    if not os.path.exists(path):
        file_selection = None
        if create_directory:
            try:
                os.makedirs(path, exist_ok=True)
            except OSError as err:
                self.fm.notify(err, bad=True)
                return
            target_directory = path
        else:
            # Give benefit of the doubt.
            potential_parent = os.path.dirname(path)
            if os.path.exists(potential_parent) and os.path.isdir(potential_parent):
                target_directory = potential_parent
            else:
                self.fm.notify("Unable to resolve given path.", bad=True)
                return
    elif os.path.isdir(path):
        file_selection = None
        target_directory = path
    else:
        file_selection = path
        target_directory = os.path.dirname(path)

    for name in self.fm.tabs:
        tab = self.fm.tabs[name]
        # Is a tab already open?
        if tab.path == target_directory:
            self.fm.tab_open(name=name)
            if file_selection:
                self.fm.select_file(file_selection)
            return

    self.fm.tab_new(path=target_directory)
    if file_selection:
        self.fm.select_file(file_selection)

def hook_ready(fm):
    import ranger.core.actions
    ranger.core.actions.Actions.tab_switch = tab_switch
    fm.commands.load_commands_from_object(fm, ["tab_switch"])
    return old_hook_ready(fm)

ranger.api.hook_ready = hook_ready

