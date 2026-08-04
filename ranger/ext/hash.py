# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

from os import listdir, readlink
from os.path import dirname, getsize, isdir, islink, join
from hashlib import sha256

# pylint: disable=invalid-name


def hash_chunks(filepath, h=None):
    if not h:
        h = sha256()
    if islink(filepath):
        # Finding duplicates is about saving space so we consider symlinks to
        # be their own thing, not duplicates of their targets.
        h.update(
            "symlink to {0}".format(
                join(dirname(filepath), readlink(filepath))
            ).encode("utf-8")
        )
        yield h.hexdigest()
    elif isdir(filepath):
        h.update(filepath.encode("utf-8"))
        yield h.hexdigest()
        for fp in listdir(filepath):
            for fp_chunk in hash_chunks(join(filepath, fp), h=h):
                yield fp_chunk
    elif getsize(filepath) == 0:
        yield h.hexdigest()
    else:
        with open(filepath, 'rb') as f:
            # Read the file in ~64KiB chunks (multiple of sha256's block
            # size that works well enough with HDDs and SSDs)
            for chunk in iter(lambda: f.read(h.block_size * 1024), b''):
                h.update(chunk)
                yield h.hexdigest()
