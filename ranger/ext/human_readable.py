# Copyright (C) 2009-2013  Roman Zimbelmann <hut@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

def human_readable(byte, separator=' '):
    """Convert a large number of bytes to an easily readable format.

    >>> human_readable(54)
    '54 B'
    >>> human_readable(1500)
    '1.46 K'
    >>> human_readable(2 ** 20 * 1023)
    '1023 M'
    """

    # I know this can be written much shorter, but this long version
    # performs much better than what I had before.  If you attempt to
    # shorten this code, take performance into consideration.
    if byte <= 0:
        return '0'
    if byte < 2**10:
        return '%d%sB'   % (byte, separator)
    if byte < 2**10 * 999:
        return '%.3g%sK' % (byte / 2**10.0, separator)
    if byte < 2**20:
        return '%.4g%sK' % (byte / 2**10.0, separator)
    if byte < 2**20 * 999:
        return '%.3g%sM' % (byte / 2**20.0, separator)
    if byte < 2**30:
        return '%.4g%sM' % (byte / 2**20.0, separator)
    if byte < 2**30 * 999:
        return '%.3g%sG' % (byte / 2**30.0, separator)
    if byte < 2**40:
        return '%.4g%sG' % (byte / 2**30.0, separator)
    if byte < 2**40 * 999:
        return '%.3g%sT' % (byte / 2**40.0, separator)
    if byte < 2**50:
        return '%.4g%sT' % (byte / 2**40.0, separator)
    if byte < 2**50 * 999:
        return '%.3g%sP' % (byte / 2**50.0, separator)
    if byte < 2**60:
        return '%.4g%sP' % (byte / 2**50.0, separator)
    return '>9000'

if __name__ == '__main__':
    import doctest
    doctest.testmod()
