# Copyright (C) 2009-2013  Roman Zimbelmann <hut@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

# prepend __ to arguments because one might use "args"
# or "keywords" as a keyword argument.

class OpenStruct(dict):
    """The fusion of dict and struct"""
    def __init__(self, *__args, **__keywords):
        dict.__init__(self, *__args, **__keywords)
        self.__dict__ = self
