# Copyright (C) 2009-2013  Roman Zimbelmann <hut@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

"""Shared objects contain singletons for shared use."""

from ranger.ext.lazy_property import lazy_property

class FileManagerAware(object):
    """Subclass this to gain access to the global "FM" object."""
    @staticmethod
    def _setup(fm):
        FileManagerAware.fm = fm

class SettingsAware(object):
    """Subclass this to gain access to the global "SettingObject" object."""
    @staticmethod
    def _setup(settings):
        SettingsAware.settings = settings

class EnvironmentAware(object):  # COMPAT
    """DO NOT USE.  This is for backward compatibility only."""
    @lazy_property
    def env(self):
        from ranger.core.environment import Environment
        return Environment(".")
