# Compatible with ranger 1.6.*
#
# This plugin hides the directories "boot", "sbin", "proc" and "sys" in the
# root directory.

# Save the original filter function
import ranger.fsobject.directory
old_accept_file = ranger.fsobject.directory.accept_file

# Define a new one
def custom_accept_file(fname, directory, hidden_filter, name_filter):
       if hidden_filter and directory.path == '/' and fname in ('boot', 'sbin', 'proc', 'sys'):
               return False
       else:
               return old_accept_file(fname, directory, hidden_filter, name_filter)

# Overwrite the old function
import ranger.fsobject.directory
ranger.fsobject.directory.accept_file = custom_accept_file
