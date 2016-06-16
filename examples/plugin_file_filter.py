# Compatible since ranger 1.7.0 (git commit c82a8a76989c)
#
# This plugin hides the directories "/boot", "/sbin", "/proc" and "/sys" unless
# the "show_hidden" option is activated.

# Save the original filter function
import ranger.container.directory
old_accept_file = ranger.container.directory.accept_file

HIDE_FILES = ("/boot", "/sbin", "/proc", "/sys")

# Define a new one


def custom_accept_file(file, filters):
    if not file.fm.settings.show_hidden and file.path in HIDE_FILES:
        return False
    else:
        return old_accept_file(file, filters)

# Overwrite the old function
import ranger.container.directory
ranger.container.directory.accept_file = custom_accept_file
