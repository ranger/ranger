# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# Based on http://blog.pythonisito.com/2008/08/lazy-descriptors.html

from __future__ import (absolute_import, division, print_function)


class lazy_property(object):  # pylint: disable=invalid-name,too-few-public-methods
    """A @property-like decorator with lazy evaluation

    >>> class Foo:
    ...     @lazy_property
    ...     def answer(self):
    ...         print("calculating answer...")
    ...         return 2*3*7
    >>> foo = Foo()
    >>> foo.answer
    calculating answer...
    42
    >>> foo.answer
    42
    >>> foo.answer__reset()
    >>> foo.answer
    calculating answer...
    42
    >>> foo.answer
    42

    Avoid interaction between multiple objects:

    >>> bar = Foo()
    >>> bar.answer
    calculating answer...
    42
    >>> foo.answer__reset()
    >>> bar.answer
    42
    """

    def __init__(self, method):
        self._method = method
        self.__name__ = method.__name__
        self.__doc__ = method.__doc__

    def __get__(self, obj, cls=None):
        if obj is None:  # to fix issues with pydoc
            return None

        def reset_function():
            setattr(obj, self.__name__, self)
            del obj.__dict__[self.__name__]  # force "__get__" being called

        obj.__dict__[self.__name__ + "__reset"] = reset_function
        result = self._method(obj)
        obj.__dict__[self.__name__] = result
        return result


if __name__ == '__main__':
    import doctest
    doctest.testmod()
