# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)


# Similar to functools.lru_cache of python3
def cached_function(fnc):
    cache = {}

    def inner_cached_function(*args):
        try:
            return cache[args]
        except KeyError:
            value = fnc(*args)
            cache[args] = value
            return value
    inner_cached_function._cache = cache  # pylint: disable=protected-access
    return inner_cached_function


# For use in ranger.vfs:
def cache_until_outdated(function):
    """
    Cache a method until self.modification_time increases

    >>> class File(object):
    ...     def __init__(self):
    ...         self.modification_time = 0
    ...
    ...     @cache_until_outdated
    ...     def get_something(self):
    ...         print('loading...')
    >>> file = File()
    >>> file.get_something()  # should load on the first call
    loading...
    >>> file.get_something()  # shouldn't load, since it's cached already
    >>> file.modification_time = 42  # simulate update
    >>> file.get_something()  # should load again now
    loading...
    >>> file.get_something()  # shouldn't load anymore
    """

    function._last_update_time = -1  # pylint: disable=protected-access
    function._cached_value = None  # pylint: disable=protected-access

    def inner_cached_function(self, *args, **kwargs):
        last_change_time = self.modification_time
        if last_change_time > function._last_update_time:  # pylint: disable=protected-access
            value = function(self, *args, **kwargs)
            function._cached_value = value  # pylint: disable=protected-access
            function._last_update_time = last_change_time  # pylint: disable=protected-access
            return value

        return function._cached_value  # pylint: disable=protected-access

    return inner_cached_function


if __name__ == '__main__':
    import doctest
    doctest.testmod()
