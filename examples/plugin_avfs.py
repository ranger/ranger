# Tested with ranger 1.9.1
#
# A very simple and possibly buggy support for AVFS
# (http://avf.sourceforge.net/), that allows ranger to handle
# archives.
#
# Run `:avfs' to browse the selected archive.

from __future__ import (absolute_import, division, print_function)

import os
import os.path

from ranger.api.commands import Command


class avfs(Command):  # pylint: disable=invalid-name
    avfs_root = os.path.join(os.environ["HOME"], ".avfs")
    avfs_suffix = "#"

    def execute(self):
        if os.path.isdir(self.avfs_root):
            archive_directory = "".join([
                self.avfs_root,
                self.fm.thisfile.path,
                self.avfs_suffix,
            ])
            if os.path.isdir(archive_directory):
                self.fm.cd(archive_directory)
            else:
                self.fm.notify("This file cannot be handled by avfs.", bad=True)
        else:
            self.fm.notify("Install `avfs' and run `mountavfs' first.", bad=True)
