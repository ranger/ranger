# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

import os

SUFFIX = '_'


def get_safe_path(dst):
    if not os.path.exists(dst):
        return dst
    if not dst.endswith(SUFFIX):
        dst += SUFFIX
        if not os.path.exists(dst):
            return dst
    n = 0
    test_dst = dst + str(n)
    while os.path.exists(test_dst):
        n += 1
        test_dst = dst + str(n)

    return test_dst
