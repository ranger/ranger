# Tested with ranger 1.9.3

from __future__ import (absolute_import, division, print_function)

import subprocess

from ranger.api.commands import Command
from ranger.config.commands import scout
from ranger.ext.rifle import Rifle


old_execute = Rifle.execute

class sxiv_select(Command):
    """:sxiv_select

    Opens sxiv in thumb mode and marked files from him will be selected in ranger.
    If one file was mark, ranger move cursot to this file.
    If you have a few files selected in ranger and run this command, sxiv opens with this files.
    """
    def execute(self):
        nl_sep = {'arg': '', 'split': '\n'}
        result_sep = nl_sep

        selected_files = self.fm.thisdir.get_selection()
        if len(selected_files) > 1:
            images = selected_files
        else:
            images = [f for f in self.fm.thisdir.files if f.image]
        # Create subprocess for sxiv and pipeout in whatever
        sxiv_args = ['-o', '-t', '--'] + [i.relative_path for i in images]
        process = subprocess.Popen(['sxiv'] + sxiv_args,
                universal_newlines=True,
                stdout=subprocess.PIPE)
        (pipe_out, _) = process.communicate()
        raw_out = pipe_out.split(result_sep['split'])
        # Delete empty
        marked_files = list(filter(None, raw_out))

        if len(marked_files) > 1:
            for node_f in images:
                if node_f.relative_path in marked_files:
                    node_f.mark_set(True)
            self.fm.ui.redraw_window()
        elif len(marked_files) == 1:
            scout_obj = scout("-ts " + marked_files[0])
            scout_obj.execute()

def sxiv_open_with(self, files, number=0, label=None, flags="", mimetype=None):
    """
    Hooking for sxiv_select option from rifle menu,
    which handle call of not exist programm and run command sxiv_select.
    """

    cmd = ""
    for count, cmd, lbl, _flags in self.list_commands(files, mimetype):
        if label and label == lbl or not label and count == number:
            cmd = self.hook_command_preprocessing(cmd)
            break
    else:
        from ranger.ext.get_executables import get_executables
        if label and label in get_executables():
            cmd = '%s "$@"' % label

    if cmd == "sxiv_select":
        sxiv_obj = sxiv_select("")
        sxiv_obj.execute()
    else:
        global old_execute
        old_execute(self, files, number, label, flags, mimetype)


Rifle.execute = sxiv_open_with
