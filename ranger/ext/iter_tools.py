# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from collections import deque


def flatten(lst):
    """Flatten an iterable.

    All contained tuples, lists, deques and sets are replaced by their
    elements and flattened as well.

    >>> l = [1, 2, [3, [4], [5, 6]], 7]
    >>> list(flatten(l))
    [1, 2, 3, 4, 5, 6, 7]
    >>> list(flatten(()))
    []
    """
    for elem in lst:
        if isinstance(elem, (tuple, list, set, deque)):
            for subelem in flatten(elem):
                yield subelem
        else:
            yield elem


def unique(iterable):
    """Return an iterable of the same type which contains unique items.

    This function assumes that:
    type(iterable)(list(iterable)) == iterable
    which is true for tuples, lists and deques (but not for strings)

    >>> unique([1, 2, 3, 1, 2, 3, 4, 2, 3, 4, 1, 1, 2])
    [1, 2, 3, 4]
    >>> unique(('w', 't', 't', 'f', 't', 'w'))
    ('w', 't', 'f')
    """
    already_seen = []
    for item in iterable:
        if item not in already_seen:
            already_seen.append(item)
    return type(iterable)(already_seen)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
