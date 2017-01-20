# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""Shared objects contain singletons for shared use."""

from __future__ import (absolute_import, print_function)

from ranger.ext.lazy_property import lazy_property  # NOQA pylint: disable=unused-import


class FileManagerAware(object):  # pylint: disable=too-few-public-methods
    """Subclass this to gain access to the global "FM" object."""
    @staticmethod
    def _setup(fm):
        FileManagerAware.fm = fm


class SettingsAware(object):  # pylint: disable=too-few-public-methods
    """Subclass this to gain access to the global "SettingObject" object."""
    @staticmethod
    def _setup(settings):
        SettingsAware.settings = settings
