# -*- coding: utf-8 -*-
# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# Author: Wojciech Siewierski <wojciech.siewierski@onet.pl>, 2018

from __future__ import (absolute_import, division, print_function)

import re
import mimetypes
# pylint: disable=invalid-name
try:
    from itertools import izip_longest as zip_longest
except ImportError:
    from itertools import zip_longest
# pylint: enable=invalid-name
from os.path import abspath

from ranger.container.directory import accept_file, InodeFilterConstants
from ranger.core.shared import FileManagerAware
from ranger.ext.hash import hash_chunks

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
        return "<Filter: name =~ /{pat}/>".format(pat=self.pattern)


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
        return "<Filter: mimetype =~ /{pat}/>".format(pat=self.pattern)


@stack_filter("hash")
class HashFilter(BaseFilter, FileManagerAware):
    def __init__(self, filepath=None):
        if filepath is None:
            self.filepath = self.fm.thisfile.path
        else:
            self.filepath = filepath
        if self.filepath is None:
            self.fm.notify("Error: No file selected for hashing!", bad=True)
        # TODO: Lazily generated list would be more efficient, a generator
        #       isn't enough because this object is reused for every fsobject
        #       in the current directory.
        self.filehash = list(hash_chunks(abspath(self.filepath)))

    def __call__(self, fobj):
        for (chunk1, chunk2) in zip_longest(self.filehash,
                                            hash_chunks(fobj.path),
                                            fillvalue=''):
            if chunk1 != chunk2:
                return False
        return True

    def __str__(self):
        return "<Filter: hash {fp}>".format(fp=self.filepath)


def group_by_hash(fsobjects):
    hashes = {}
    for fobj in fsobjects:
        chunks = hash_chunks(fobj.path)
        chunk = next(chunks)
        while chunk in hashes:
            for dup in hashes[chunk]:
                _, dup_chunks = dup
                try:
                    hashes[next(dup_chunks)] = [dup]
                    hashes[chunk].remove(dup)
                except StopIteration:
                    pass
            try:
                chunk = next(chunks)
            except StopIteration:
                hashes[chunk].append((fobj, chunks))
                break
        else:
            hashes[chunk] = [(fobj, chunks)]

    groups = []
    for dups in hashes.values():
        group = []
        for (dup, _) in dups:
            group.append(dup)
        if group:
            groups.append(group)

    return groups


@stack_filter("duplicate")
class DuplicateFilter(BaseFilter, FileManagerAware):
    def __init__(self, _):
        self.duplicates = self.get_duplicates()

    def __call__(self, fobj):
        return fobj in self.duplicates

    def __str__(self):
        return "<Filter: duplicate>"

    def get_duplicates(self):
        duplicates = set()
        for dups in group_by_hash(self.fm.thisdir.files_all):
            if len(dups) >= 2:
                duplicates.update(dups)
        return duplicates


@stack_filter("unique")
class UniqueFilter(BaseFilter, FileManagerAware):
    def __init__(self, _):
        self.unique = self.get_unique()

    def __call__(self, fobj):
        return fobj in self.unique

    def __str__(self):
        return "<Filter: unique>"

    def get_unique(self):
        unique = set()
        for dups in group_by_hash(self.fm.thisdir.files_all):
            try:
                unique.add(min(dups, key=lambda fobj: fobj.stat.st_ctime))
            except ValueError:
                pass
        return unique


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
        return "<Filter: type == '{ft}'>".format(ft=self.filetype)


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
        return "<Filter: {comp}>".format(
            comp=" or ".join(map(str, self.subfilters)))

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
        return "<Filter: {comp}>".format(
            comp=" and ".join(map(str, self.subfilters)))

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
        return "<Filter: not {exp}>".format(exp=str(self.subfilter))

    def decompose(self):
        return [self.subfilter]
