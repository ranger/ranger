# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

from datetime import datetime

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

    units = ['B', 'K', 'M', 'G', 'T', 'P']

    # handle automatically_count_files false
    if byte is None:
        return ''

    if SettingsAware.settings.size_in_bytes:
        return format(byte, 'n')  # 'n' = locale-aware separator.

    [formatted_number, unit_index] = _preformat_bytes(byte)
    if unit_index is None:
        return formatted_number
    return '{0:s}{1:s}{2:s}'.format(formatted_number, separator, units[unit_index])


def _preformat_bytes(byte):  # pylint: disable=too-many-return-statements
    # I know this can be written much shorter, but this long version
    # performs much better than what I had before.  If you attempt to
    # shorten this code, take performance into consideration.
    #
    # Revisit of 2020: In order to implement file copy speed with
    # correct units, this had to be refactored. While we are at it,
    # let's use format functions. It now has about 3 times worse
    # performance than the original solution using %-formatting. The
    # justification here is this function doesn't account for much
    # execution time in the overall rendering time of Ranger. The
    # function was benchmarked and profiled. Ranger as a whole was
    # tested on a weak hardware and a user experience degradation
    # was not perceptible. I think we did our best to take
    # performance into consideration.

    if byte <= 0:
        return ('0', None)
    if byte < 2**10:
        return ('{0:d}'.format(byte), 0)
    if byte < 2**10 * 999:
        return ('{0:.3g}'.format(byte / 2**10), 1)
    if byte < 2**20:
        return ('{0:.4g}'.format(byte / 2**10), 1)
    if byte < 2**20 * 999:
        return ('{0:.3g}'.format(byte / 2**20), 2)
    if byte < 2**30:
        return ('{0:.4g}'.format(byte / 2**20), 2)
    if byte < 2**30 * 999:
        return ('{0:.3g}'.format(byte / 2**30), 3)
    if byte < 2**40:
        return ('{0:.4g}'.format(byte / 2**30), 3)
    if byte < 2**40 * 999:
        return ('{0:.3g}'.format(byte / 2**40), 4)
    if byte < 2**50:
        return ('{0:.4g}'.format(byte / 2**40), 4)
    if byte < 2**50 * 999:
        return ('{0:.3g}'.format(byte / 2**50), 5)
    if byte < 2**60:
        return ('{0:.4g}'.format(byte / 2**50), 5)
    return ('>9000', None)


def human_readable_time(timestamp):
    """Convert a timestamp to an easily readable format.
    """
    # Hard to test because it's relative to ``now()``
    date = datetime.fromtimestamp(timestamp)
    datediff = datetime.now().date() - date.date()
    if datediff.days >= 365:
        return date.strftime("%-d %b %Y")
    elif datediff.days >= 7:
        return date.strftime("%-d %b")
    elif datediff.days >= 1:
        return date.strftime("%a")
    return date.strftime("%H:%M")


if __name__ == '__main__':

    # XXX: This mock class is a temporary (as of 2019-01-27) hack.
    class SettingsAwareMock(object):  # pylint: disable=too-few-public-methods
        class settings(object):  # pylint: disable=invalid-name,too-few-public-methods
            size_in_bytes = False
    SettingsAware = SettingsAwareMock  # noqa: F811

    import doctest
    import sys
    sys.exit(doctest.testmod()[0])
