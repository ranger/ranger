# Compatible since ranger 1.7.0 (git commit c82a8a76989c)
#
# This plugin hides the directories "/boot", "/sbin", "/proc" and "/sys" unless
# the "show_hidden" option is activated.

# Save the original filter function

from __future__ import (absolute_import, division, print_function)

import ranger.container.directory


ACCEPT_FILE_OLD = ranger.container.directory.accept_file

HIDE_FILES = ("/boot", "/sbin", "/proc", "/sys")


# Define a new one
def custom_accept_file(fobj, filters):
    if not fobj.fm.settings.show_hidden and fobj.path in HIDE_FILES:
        return False
    return ACCEPT_FILE_OLD(fobj, filters)


# Overwrite the old function
ranger.container.directory.accept_file = custom_accept_file
