from __future__ import (absolute_import, division, print_function)

import operator

from ranger.container.fsobject import FileSystemObject


class MockFM(object):  # pylint: disable=too-few-public-methods
    """Used to fulfill the dependency by FileSystemObject."""

    default_linemodes = []


def create_filesystem_object(path):
    """Create a FileSystemObject without an fm object."""
    fso = FileSystemObject.__new__(FileSystemObject)
    fso.fm = MockFM()
    fso.__init__(path)
    return fso


def test_basename_natural1():
    """Test filenames without extensions."""
    fsos = [
        create_filesystem_object(path)
        for path in (
            "0", "1", "2", "3",
            "10", "11", "12", "13",
            "100", "101", "102", "103",
            "110", "111", "112", "113",
            "hello",
            "hello1", "hello2",
            "hello11", "hello12",
            "hello100", "hello101", "hello111", "hello112",
        )
    ]
    assert fsos == sorted(fsos[::-1], key=operator.attrgetter("basename_natural"))
    assert fsos == sorted(fsos[::-1], key=operator.attrgetter("basename_natural_lower"))


def test_basename_natural2():
    """Test filenames with extensions."""
    fsos = [
        create_filesystem_object(path)
        for path in (
            "hello", "hello.txt",
            "hello0.txt", "hello1.txt", "hello2.txt", "hello3.txt"
            "hello10.txt", "hello11.txt", "hello12.txt", "hello13.txt"
            "hello100.txt", "hello101.txt", "hello102.txt", "hello103.txt"
            "hello110.txt", "hello111.txt", "hello112.txt", "hello113.txt"
        )
    ]
    assert fsos == sorted(fsos[::-1], key=operator.attrgetter("basename_natural"))
    assert fsos == sorted(fsos[::-1], key=operator.attrgetter("basename_natural_lower"))
