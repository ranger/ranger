from __future__ import absolute_import
import sys


MACRO_FAIL = "<\x01\x01MACRO_HAS_NO_VALUE\x01\01>"


def macro_val(thunk, fallback=MACRO_FAIL):
    try:
        return thunk()
    except AttributeError:
        return fallback


try:
    from collections.abc import MutableMapping  # pylint: disable=no-name-in-module
except ImportError:
    from collections import MutableMapping


class MacroDict(MutableMapping):
    """Mapping that returns a fallback value when thunks error

    Macros can be used in scenarios where several attributes aren't
    initialized yet. To avoid errors in these cases we have to delay the
    evaluation of these attributes using ``lambda``s. This
    ``MutableMapping`` evaluates these thunks before returning them
    replacing them with a fallback value if necessary.

    For convenience it also catches ``TypeError`` so you can store
    non-callable values without thunking.

    >>> m = MacroDict()
    >>> o = type("", (object,), {})()
    >>> o.existing_attribute = "I exist!"

    >>> m['a'] = "plain value"
    >>> m['b'] = lambda: o.non_existent_attribute
    >>> m['c'] = lambda: o.existing_attribute

    >>> m['a']
    'plain value'
    >>> m['b']
    '<\\x01\\x01MACRO_HAS_NO_VALUE\\x01\\x01>'
    >>> m['c']
    'I exist!'
    """

    def __init__(self, *args, **kwargs):
        super(MacroDict, self).__init__()
        self.__dict__.update(*args, **kwargs)

    def __setitem__(self, key, value):
        try:
            real_val = value()
            if real_val is None:
                real_val = MACRO_FAIL
        except AttributeError:
            real_val = MACRO_FAIL
        except TypeError:
            real_val = value
        self.__dict__[key] = real_val

    def __getitem__(self, key):
        return self.__dict__[key]

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


if __name__ == '__main__':
    import doctest
    sys.exit(doctest.testmod()[0])
