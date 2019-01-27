# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# Based on http://blog.pythonisito.com/2008/08/lazy-descriptors.html

from __future__ import (absolute_import, division, print_function)


class lazy_property(object):  # pylint: disable=invalid-name,too-few-public-methods
    """A @property-like decorator with lazy evaluation

    >>> class Foo:
    ...     counter = 0
    ...     @lazy_property
    ...     def answer(self):
    ...         Foo.counter += 1
    ...         return Foo.counter
    >>> foo = Foo()
    >>> foo.answer
    1
    >>> foo.answer
    1
    >>> foo.answer__reset()
    >>> foo.answer
    2
    >>> foo.answer
    2

    Avoid interaction between multiple objects:

    >>> bar = Foo()
    >>> bar.answer
    3
    >>> foo.answer__reset()
    >>> bar.answer
    3
    """

    def __init__(self, method):
        self._method = method
        self.__name__ = method.__name__
        self.__doc__ = method.__doc__

    def __get__(self, obj, cls=None):
        if obj is None:  # to fix issues with pydoc
            return None

        reset_function_name = self.__name__ + "__reset"

        if not hasattr(obj, reset_function_name):
            def reset_function():
                setattr(obj, self.__name__, self)
                del obj.__dict__[self.__name__]  # force "__get__" being called
            obj.__dict__[reset_function_name] = reset_function

        result = self._method(obj)
        obj.__dict__[self.__name__] = result
        return result


if __name__ == '__main__':
    import doctest
    import sys
    sys.exit(doctest.testmod()[0])
