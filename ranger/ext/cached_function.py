# Copyright (C) 2012-2013  Roman Zimbelmann <hut@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

def cached_function(fnc):
    cache = {}
    def inner_cached_function(*args):
        try:
            return cache[args]
        except:
            value = fnc(*args)
            cache[args] = value
            return value
    inner_cached_function._cache = cache
    return inner_cached_function

