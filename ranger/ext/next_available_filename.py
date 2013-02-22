# Copyright (C) 2011-2013  Roman Zimbelmann <hut@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

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
