# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, print_function)


def cached_function(fnc):
    cache = {}

    def inner_cached_function(*args):
        try:
            return cache[args]
        except Exception:
            value = fnc(*args)
            cache[args] = value
            return value
    inner_cached_function._cache = cache  # pylint: disable=protected-access
    return inner_cached_function
