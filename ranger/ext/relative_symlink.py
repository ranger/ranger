# Copyright (C) 2009-2013  Roman Zimbelmann <hut@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

from os import symlink, sep

def relative_symlink(src, dst):
    common_base = get_common_base(src, dst)
    symlink(get_relative_source_file(src, dst, common_base), dst)

def get_relative_source_file(src, dst, common_base=None):
    if common_base is None:
        common_base = get_common_base(src, dst)
    return '../' * dst.count('/', len(common_base)) + src[len(common_base):]

def get_common_base(src, dst):
    if not src or not dst:
        return '/'
    i = 0
    while True:
        new_i = src.find(sep, i + 1)
        if new_i == -1:
            break
        if not dst.startswith(src[:new_i + 1]):
            break
        i = new_i
    return src[:i + 1]
