# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

import os.path


def next_available_filename(fname, directory="."):
    existing_files = os.listdir(directory)

    if fname not in existing_files:
        return fname
    if not fname.endswith("_"):
        fname += "_"
        if fname not in existing_files:
            return fname

    for i in range(1, len(existing_files) + 1):
        if fname + str(i) not in existing_files:
            return fname + str(i)
