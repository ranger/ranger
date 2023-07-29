# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

import shutil
from subprocess import check_output, CalledProcessError
from ranger import PY3


def which(cmd):
    if PY3:
        return shutil.which(cmd)

    try:
        return check_output(["command", "-v", cmd])
    except CalledProcessError:
        return None
