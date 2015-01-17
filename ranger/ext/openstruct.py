# Copyright (C) 2009-2013  Roman Zimbelmann <hut@hut.pm>
# This software is distributed under the terms of the GNU GPL version 3.

import collections

# prepend __ to arguments because one might use "args"
# or "keywords" as a keyword argument.

class OpenStruct(dict):
    """The fusion of dict and struct"""
    def __init__(self, *__args, **__keywords):
        dict.__init__(self, *__args, **__keywords)
        self.__dict__ = self


class DefaultOpenStruct(collections.defaultdict):
    """The fusion of dict and struct, with default values"""
    def __init__(self, *__args, **__keywords):
        collections.defaultdict.__init__(self, None, *__args, **__keywords)
        self.__dict__ = self

    def __getattr__(self, name):
        if name not in self.__dict__:
            return None
        else:
            return self.__dict__[name]
