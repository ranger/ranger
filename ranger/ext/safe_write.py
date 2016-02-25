#!/usr/bin/env python
# License: GNU GPL version 3, see the file "AUTHORS" for details.

import os


def safe_write(path, content):
    """
    write content to path safely, avoiding no-free-space issues
    """
    if path is None:
        return

    # Find targets
    real_path = os.path.realpath(path)
    if os.path.exists(real_path):
        temp_path = real_path + '.new'
    else:
        temp_path = real_path

    # Stop if targets are unwritable
    if not all(not os.path.exists(p) or os.access(p, os.W_OK) \
            for p in set([temp_path, real_path])):
        return

    # Open file and write the content
    try:
        filestream = open(temp_path, 'w')
    except OSError:
        return
    try:
        filestream.write(content)
    except UnicodeEncodeError:
        pass
    try:
        filestream.close()
    except IOError:
        pass

    # Assign the old permissions
    old_perms = os.stat(real_path)
    try:
        os.chown(temp_path, old_perms.st_uid, old_perms.st_gid)
        os.chmod(temp_path, old_perms.st_mode)
    except OSError:
        pass

    # Replace the actual file with the new file, if necessary
    if temp_path != real_path:
        os.rename(temp_path, real_path)
