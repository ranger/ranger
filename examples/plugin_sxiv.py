# Tested with ranger 1.9.3

from __future__ import (absolute_import, division, print_function)
from hashlib import sha512

import subprocess

from ranger.api.commands import Command
from ranger.ext.rifle import Rifle
from ranger.core.actions import Actions
import ranger


old_execute = Rifle.execute

class sxiv_select(Command):
    """:sxiv_select

    Opens sxiv in thumb mode and if any files was mark from him will be selected in ranger.
    If one file was mark, ranger move cursor to this file.
    If you have a few files selected in ranger and run this command, sxiv opens with this files.
    Image and video are supported.
    """
    def execute(self):
        nl_sep = {'arg': '', 'split': '\n'}
        result_sep = nl_sep
        sxiv_args = []

        selected_files = self.fm.thisdir.get_selection()
        if len(selected_files) > 1:
            images = selected_files
        else:
            images = [f for f in self.fm.thisdir.files if f.image or f.video]
        if not images:
            self.fm.notify("Can't find images or videos.")
            return

        # Open sxiv with current file, if it is in the selected files.
        if self.fm.thisfile in images:
            image_index = images.index(self.fm.thisfile) + 1
            sxiv_args += ['-n %d' % image_index]

        # -o     Write list of all marked files to standard output when quitting.
        # -t     Start in thumbnail mode.
        # --     Separate flags and file list.
        sxiv_args += ['-o', '-t', '--']
        sxiv_args += ["/".join([ranger.args.cachedir, Actions.sha512_encode(i.path)])
                      if i.video else i.relative_path
                      for i in images]


        # Create subprocess for sxiv and pipeout in whatever
        process = subprocess.Popen(['sxiv'] + sxiv_args,
                universal_newlines=True,
                stdout=subprocess.PIPE)
        (pipe_out, _) = process.communicate()
        raw_out = pipe_out.split(result_sep['split'])
        # Delete empty
        marked_files = list(filter(None, raw_out))

        self.fm.thisdir.mark_all(False)
        files_to_mark = []
        if len(marked_files) >= 1:
            for fobj in images:
                filename = "/".join([ranger.args.cachedir,
                    Actions.sha512_encode(fobj.path)]) if fobj.video else fobj.relative_path
                if filename in marked_files:
                    if len(files_to_mark) == 0:
                        self.fm.cd(fobj.path)
                    if len(marked_files) > 1:
                        files_to_mark.append(fobj)

        for fobj in files_to_mark:
            self.fm.thisdir.mark_item(fobj, True)

        self.fm.ui.redraw_window()

class get_all_preview(Command):
    def execute(self):
        for fobj in self.fm.thisdir.files:
            if fobj.video:
                fobj.get_preview_source(-1,-1)

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
