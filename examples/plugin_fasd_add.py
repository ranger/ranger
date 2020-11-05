# This plugin adds opened files to `fasd`

from __future__ import (absolute_import, division, print_function)

import subprocess

import ranger.api
from ranger.ext.spawn import check_output


HOOK_INIT_OLD = ranger.api.hook_init


def hook_init(fm):
    def fasd_add():
        for fobj in fm.thistab.get_selection():
            try:
                check_output(['fasd', '--add', fobj.path])
            except subprocess.CalledProcessError:
                pass
    fm.signal_bind('execute.before', fasd_add)
    return HOOK_INIT_OLD(fm)


ranger.api.hook_init = hook_init
