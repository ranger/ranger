# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# pylint: disable=protected-access

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
    >>> file.modification_time = 23
    >>> file.get_something()  # shouldn't load, since mod time decresased
    >>> file2 = File()
    >>> file2.get_something()
    loading...
    """

    attrname_update_time = '_last_update_time__%s' % function.__name__
    attrname_value = '_last_value__%s' % function.__name__

    def inner_cached_function(self, *args, **kwargs):
        last_change_time = self.modification_time
        last_update_time = getattr(self, attrname_update_time, -1)
        if last_change_time > last_update_time:
            value = function(self, *args, **kwargs)
            setattr(self, attrname_value, value)
            setattr(self, attrname_update_time, last_change_time)
            return value

        assert hasattr(self, attrname_value), \
            "Attempted to read cached value before caching it"
        return getattr(self, attrname_value)

    return inner_cached_function


if __name__ == '__main__':
    import doctest
    doctest.testmod()
