from __future__ import absolute_import
import collections
import os

from ranger.core import main


def test_get_paths():
    args_tuple = collections.namedtuple('args', 'paths')
    args = args_tuple(paths=None)

    paths = main.get_paths(args)

    for path in paths:
        assert os.path.exists(path)


if __name__ == '__main__':
    test_get_paths()
