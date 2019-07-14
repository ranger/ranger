# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

import os

APPENDIX = '_'


def get_safe_path_classic(dst):
    if not os.path.exists(dst):
        return dst
    if not dst.endswith(APPENDIX):
        dst += APPENDIX
        if not os.path.exists(dst):
            return dst
    n = 0
    test_dst = dst + str(n)
    while os.path.exists(test_dst):
        n += 1
        test_dst = dst + str(n)

    return test_dst


def get_safe_path(dst):
    if not os.path.exists(dst):
        return dst

    dst_name, dst_ext = os.path.splitext(dst)

    if not dst_name.endswith(APPENDIX):
        dst_name += APPENDIX
        if not os.path.exists(dst_name + dst_ext):
            return dst_name + dst_ext
    n = 0
    test_dst = dst_name + str(n)
    while os.path.exists(test_dst + dst_ext):
        n += 1
        test_dst = dst_name + str(n)

    return test_dst + dst_ext
