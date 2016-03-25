import pytest
import operator

from ranger.container.fsobject import FileSystemObject


class MockFM(object):
    """Used to fullfill the dependency by FileSystemObject."""

    default_linemodes = []


def create_filesystem_object(path):
    """Create a FileSystemObject without an fm object."""
    fso = FileSystemObject.__new__(FileSystemObject)
    fso.fm = MockFM()
    fso.__init__(path)
    return fso


def test_basename_natural1():
    """Test filenames without extensions."""
    fsos = [create_filesystem_object(path)
            for path in ("hello", "hello1", "hello2")]
    assert(fsos == sorted(fsos[::-1], key=operator.attrgetter("basename_natural")))
    assert(fsos == sorted(fsos[::-1], key=operator.attrgetter("basename_natural_lower")))


def test_basename_natural2():
    """Test filenames with extensions."""
    fsos = [create_filesystem_object(path)
            for path in ("hello", "hello.txt", "hello1.txt", "hello2.txt")]
    assert(fsos == sorted(fsos[::-1], key=operator.attrgetter("basename_natural")))
    assert(fsos == sorted(fsos[::-1], key=operator.attrgetter("basename_natural_lower")))
