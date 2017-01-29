# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""Shared objects contain singletons for shared use."""

from __future__ import (absolute_import, division, print_function)


class FileManagerAware(object):  # pylint: disable=too-few-public-methods
    """Subclass this to gain access to the global "FM" object."""
    @staticmethod
    def fm_set(fm):
        FileManagerAware.fm = fm


class SettingsAware(object):  # pylint: disable=too-few-public-methods
    """Subclass this to gain access to the global "SettingObject" object."""
    @staticmethod
    def settings_set(settings):
        SettingsAware.settings = settings
