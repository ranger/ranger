# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

from ranger.core.shared import SettingsAware


def human_readable(byte, separator=' '):  # pylint: disable=too-many-return-statements
    """Convert a large number of bytes to an easily readable format.

    >>> human_readable(54)
    '54 B'
    >>> human_readable(1500)
    '1.46 K'
    >>> human_readable(2 ** 20 * 1023)
    '1023 M'
    """

    # handle automatically_count_files false
    if byte is None:
        return ''

    if SettingsAware.settings.size_in_bytes:
        return format(byte, 'n')  # 'n' = locale-aware separator.

    # I know this can be written much shorter, but this long version
    # performs much better than what I had before.  If you attempt to
    # shorten this code, take performance into consideration.
    if byte <= 0:
        return '0'
    if byte < 2**10:
        return '%d%sB' % (byte, separator)
    if byte < 2**10 * 999:
        return '%.3g%sK' % ((byte / 2**10), separator)
    if byte < 2**20:
        return '%.4g%sK' % ((byte / 2**10), separator)
    if byte < 2**20 * 999:
        return '%.3g%sM' % ((byte / 2**20), separator)
    if byte < 2**30:
        return '%.4g%sM' % ((byte / 2**20), separator)
    if byte < 2**30 * 999:
        return '%.3g%sG' % ((byte / 2**30), separator)
    if byte < 2**40:
        return '%.4g%sG' % ((byte / 2**30), separator)
    if byte < 2**40 * 999:
        return '%.3g%sT' % ((byte / 2**40), separator)
    if byte < 2**50:
        return '%.4g%sT' % ((byte / 2**40), separator)
    if byte < 2**50 * 999:
        return '%.3g%sP' % ((byte / 2**50), separator)
    if byte < 2**60:
        return '%.4g%sP' % ((byte / 2**50), separator)
    return '>9000'


if __name__ == '__main__':

    # XXX: This mock class is a temporary (as of 2019-01-27) hack.
    class SettingsAwareMock(object):  # pylint: disable=too-few-public-methods
        class settings(object):  # pylint: disable=invalid-name,too-few-public-methods
            size_in_bytes = False
    SettingsAware = SettingsAwareMock  # noqa: F811

    import doctest
    import sys
    sys.exit(doctest.testmod()[0])
