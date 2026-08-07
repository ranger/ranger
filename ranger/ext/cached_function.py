# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

import functools

try:
    from inspect import getfullargspec as _getargspec
except ImportError:  # Python 2
    from inspect import getargspec as _getargspec  # type: ignore[attr-defined]


# Similar to functools.lru_cache of python3.
#
# Usage:
#     @cached_function                            # unbounded cache over *args
#     @cached_function(maxsize=N)                 # LRU cache over *args
#     @cached_function(key_args=['a', 'b'])       # cache key built from the
#                                                 # named arguments only;
#                                                 # positional and keyword
#                                                 # calls key identically.
#     @cached_function(maxsize=N, key_args=[...]) # both, combined.
def cached_function(fnc=None, maxsize=None, key_args=None):
    def decorator(real_fnc):
        cache = {}
        order = []  # keys in LRU order; least-recently-used at the front
        fnc_name = getattr(real_fnc, '__name__', '<unknown>')

        if key_args is None:
            def _build_key_from_args(args, kwargs):
                if kwargs:
                    raise TypeError(
                        "cached_function: unexpected keyword arguments %r"
                        % sorted(kwargs)
                    )
                return args
            build_key = _build_key_from_args
        else:
            spec = _getargspec(real_fnc)
            arg_names = list(spec.args)
            positions = dict((n, i) for i, n in enumerate(arg_names))
            missing = [k for k in key_args if k not in positions]
            if missing:
                raise TypeError(
                    "cached_function: key_args %r not in parameters of %s()"
                    % (missing, fnc_name)
                )
            if spec.defaults:
                defaults = dict(zip(arg_names[-len(spec.defaults):], spec.defaults))
            else:
                defaults = {}
            key_arg_names = tuple(key_args)

            def _build_key_from_named(args, kwargs):
                resolved = []
                for name in key_arg_names:
                    if name in kwargs:
                        resolved.append(kwargs[name])
                    elif positions[name] < len(args):
                        resolved.append(args[positions[name]])
                    elif name in defaults:
                        resolved.append(defaults[name])
                    else:
                        raise TypeError(
                            "%s() missing required argument: %r"
                            % (fnc_name, name)
                        )
                return tuple(resolved)
            build_key = _build_key_from_named

        @functools.wraps(real_fnc)
        def wrapper(*args, **kwargs):
            key = build_key(args, kwargs)
            if key in cache:
                if maxsize is not None:
                    order.remove(key)
                    order.append(key)
                return cache[key]
            value = real_fnc(*args, **kwargs)
            cache[key] = value
            if maxsize is not None:
                order.append(key)
                while len(order) > maxsize:
                    del cache[order.pop(0)]
            return value

        # pylint: disable=protected-access
        wrapper._cache = cache  # type: ignore[reportFunctionMemberAccess]
        return wrapper

    if callable(fnc):
        return decorator(fnc)
    return decorator
