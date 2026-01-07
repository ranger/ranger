# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from collections import defaultdict

class BulkCommand(object):
    """Bulk command functions for getting and editing file attributes"""

    def get_attribute(self, file):
        """Get the attribute for the file"""

    def get_change_attribute_command(self, file, old, new):
        """Generate and return the shell command string that changes the
        file's attribute from the old value to the new one"""

class BulkCommandUnsupportedException(Exception):
    pass

def fallback_bulk_command():
    """Simply makes some noise when chosen. Temporary fallback behavior."""

    raise BulkCommandUnsupportedException

BULK_COMMAND_REGISTRY = defaultdict(fallback_bulk_command)

def register_bulk_command(nickname=None):
    """Register a bulk command by nickname if available."""

    def decorator(bulk_command_class):
        if nickname:
            registry_key = nickname
        else:
            registry_key = bulk_command_class.__name__
        BULK_COMMAND_REGISTRY[registry_key] = bulk_command_class
        return bulk_command_class
    return decorator

def get_bulk_command(registry_key):
    bulk_command_class = BULK_COMMAND_REGISTRY[registry_key]
    return bulk_command_class()
