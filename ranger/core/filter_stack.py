# -*- coding: utf-8 -*-
# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# Author: Wojciech Siewierski <wojciech.siewierski@onet.pl>, 2018

from __future__ import (absolute_import, division, print_function)

import re
import mimetypes

from ranger.container.directory import accept_file, InodeFilterConstants

# pylint: disable=too-few-public-methods


class BaseFilter(object):
    def decompose(self):
        return [self]


SIMPLE_FILTERS = {}
FILTER_COMBINATORS = {}


def stack_filter(filter_name):
    def decorator(cls):
        SIMPLE_FILTERS[filter_name] = cls
        return cls
    return decorator


def filter_combinator(combinator_name):
    def decorator(cls):
        FILTER_COMBINATORS[combinator_name] = cls
        return cls
    return decorator


@stack_filter("name")
class NameFilter(BaseFilter):
    def __init__(self, pattern):
        self.pattern = pattern
        self.regex = re.compile(pattern)

    def __call__(self, fobj):
        return self.regex.search(fobj.relative_path)

    def __str__(self):
        return "<Filter: name =~ /{}/>".format(self.pattern)


@stack_filter("mime")
class MimeFilter(BaseFilter):
    def __init__(self, pattern):
        self.pattern = pattern
        self.regex = re.compile(pattern)

    def __call__(self, fobj):
        mimetype, _ = mimetypes.guess_type(fobj.relative_path)
        if mimetype is None:
            return False
        return self.regex.search(mimetype)

    def __str__(self):
        return "<Filter: mimetype =~ /{}/>".format(self.pattern)


@stack_filter("type")
class TypeFilter(BaseFilter):
    type_to_function = {
        InodeFilterConstants.DIRS:
        (lambda fobj: fobj.is_directory),
        InodeFilterConstants.FILES:
        (lambda fobj: fobj.is_file and not fobj.is_link),
        InodeFilterConstants.LINKS:
        (lambda fobj: fobj.is_link),
    }

    def __init__(self, filetype):
        if filetype not in self.type_to_function:
            raise KeyError(filetype)
        self.filetype = filetype

    def __call__(self, fobj):
        return self.type_to_function[self.filetype](fobj)

    def __str__(self):
        return "<Filter: type == '{}'>".format(self.filetype)


@filter_combinator("or")
class OrFilter(BaseFilter):
    def __init__(self, stack):
        self.subfilters = [stack[-2], stack[-1]]

        stack.pop()
        stack.pop()

        stack.append(self)

    def __call__(self, fobj):
        # Turn logical AND (accept_file()) into a logical OR with the
        # De Morgan's laws.
        return not accept_file(
            fobj,
            ((lambda x, f=filt: not f(x))
             for filt
             in self.subfilters),
        )

    def __str__(self):
        return "<Filter: {}>".format(" or ".join(map(str, self.subfilters)))

    def decompose(self):
        return self.subfilters


@filter_combinator("and")
class AndFilter(BaseFilter):
    def __init__(self, stack):
        self.subfilters = [stack[-2], stack[-1]]

        stack.pop()
        stack.pop()

        stack.append(self)

    def __call__(self, fobj):
        return accept_file(fobj, self.subfilters)

    def __str__(self):
        return "<Filter: {}>".format(" and ".join(map(str, self.subfilters)))

    def decompose(self):
        return self.subfilters


@filter_combinator("not")
class NotFilter(BaseFilter):
    def __init__(self, stack):
        self.subfilter = stack.pop()
        stack.append(self)

    def __call__(self, fobj):
        return not self.subfilter(fobj)

    def __str__(self):
        return "<Filter: not {}>".format(str(self.subfilter))

    def decompose(self):
        return [self.subfilter]
