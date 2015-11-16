# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# Author: Wojciech Siewierski <wojciech.siewierski@onet.pl>, 2015

import os.path
import re


_compatibility = {
    'scope.sh': (1,7,9999),
    'commands.py': (1,7,9999),
    'rifle.conf': (1,7,9999),
    'rc.conf': (1,7,9999),
}


class Version(object):
    """Comparable version objects.

    >>> Version('1.7.2') < Version('1.7.2-rc2-2012-12-21') < Version('1.7.3')
    True

    >>> (1, 7, 2) < Version('1.7.2-rc2-2012-12-21') < (1, 7, 3)
    True

    >>> Version('1.7.2-rc1') < Version('1.7.2-rc2') < Version('1.7.2-rc2-2012-12-21') < (1, 7, 3)
    True

    >>> Version('1.7.2-rc2-2012-12-22') < Version('1.7.2-rc2-2012-12-21')
    False

    >>> Version('1.7.2-rc2-2012-12-22')
    (1, 7, 2, 'rc2', 2012, 12, 22)

    >>> str(Version('1.7.2-rc2-2012-12-22'))
    '1.7.2-rc2-2012-12-22'

    """
    def __init__(self, version):
        if isinstance(version, str):
            self.string = version
            self.numeric = version_string_to_tuple(version)
        else:
            self.numeric = Version
            self.string = ".".join(map(str, version))

    def __lt__(self, rhs):
        if isinstance(rhs, Version):
            return self.numeric < rhs.numeric
        else:
            return self.numeric < rhs

    def __gt__(self, rhs):
        if isinstance(rhs, Version):
            return self.numeric > rhs.numeric
        else:
            return self.numeric > rhs

    def __eq__(self, rhs):
        if isinstance(rhs, Version):
            return self.numeric == rhs.numeric
        else:
            return self.numeric == rhs

    def __str__(self):
        return self.string

    def __repr__(self):
        return str(self.numeric)


def version_string_to_tuple(version):
    """Convert a version string to easily comparable tuple of ints and strings.

    >>> version_string_to_tuple('1.7.2-rc2-2012-12-21')
    (1, 7, 2, 'rc2', 2012, 12, 21)

    Quirks: Remember to use text always in the same fields, otherwise
    the comparisons may not be as easy.

    """
    version_list = re.split(r"[-.]", version)
    def try_ints():
        for x in version_list:
            try:
                yield int(x)
            except ValueError:
                yield x
    return tuple(try_ints())


def read_version_from_file(version_file_path):
    """Try to extract a version from the first 5 lines of a file.

    The version line should match this regular expression:
    #\s*version:\s*(.*)

    i.e. contain a hash, some optional whitespace, a colon and then
    the version.

    """
    with open(version_file_path, 'r') as version_file:
        for _ in range(5):
            line = version_file.readline()
            match = re.match(r"#\s*version:\s*(.*)", line)
            if match:
                return Version(match.group(1).strip())


def outdated_configs(used_versions, needed_versions):
    """Return an iterable of tuples (file, used_version, needed_version)."""
    for config in used_versions.keys():
        if used_versions[config] is not None and used_versions[config] < needed_versions[config]:
            yield (config,
                   used_versions[config],
                   Version(needed_versions[config]))


def perform_check(config_directory):
    """Return an iterable of outdated configs in a given directory.

    See for details: outdated_configs()

    """
    used_versions = {}
    for config in _compatibility.keys():
        try:
            used_versions[config] = read_version_from_file(
                os.path.join(config_directory, config))
        except IOError:
            pass
    return outdated_configs(used_versions, _compatibility)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
