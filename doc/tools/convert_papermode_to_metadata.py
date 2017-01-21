#!/bin/python
"""
usage: ./convert_papermode_to_metadata.py

This script converts the .paperinfo CSV file in the current directory to an
equivalent .metadata.json file.

ranger used to store metadata in .paperinfo files, but that format was rather
limited, so .metadata.json files were introduced.
"""

from __future__ import (absolute_import, division, print_function)

import csv
import json
import os
import sys

if sys.version_info[0] < 3:
    input = raw_input  # NOQA pylint: disable=undefined-variable,redefined-builtin,invalid-name


FIELDS = ["name", "year", "title", "authors", "url"]


def replace(source, target):
    if not os.path.exists(source):
        print("Source file `%s' doesn't exist, skipping." % source)
        return

    # Ask for user confirmation if the target file already exists
    if os.path.exists(target):
        sys.stdout.write("Warning: target file `%s' exists! Overwrite? [y/N]")
        userinput = input()
        if not (userinput.startswith("y") or userinput.startswith("Y")):
            print("Skipping file `%s'" % source)
            return

    result = dict()

    # Read the input file and convert it to a dictionary
    with open(".paperinfo", "r") as infile:
        reader = csv.reader(infile, skipinitialspace=True)
        for lineno, row in enumerate(reader):
            if len(row) != len(FIELDS):
                print("skipping invalid row `%s' on line %d" % (row, lineno))
                continue
            name = row[0]
            entry = {}

            # Filling up the resulting entry dict
            for i, column in enumerate(row[1:]):
                if column:
                    entry[FIELDS[i + 1]] = column

            # Adding the dict if it isn't empty
            if entry:
                result[name] = entry

    # Write the obtained dictionary into the target file
    if result:
        with open(".metadata.json", "w") as outfile:
            json.dump(result, outfile, indent=2)
    else:
        print("Skipping writing `%s' due to a lack of data" % target)


if __name__ == "__main__":
    if set(['--help', '-h']) & set(sys.argv[1:]):
        print(__doc__.strip())
    else:
        replace(".paperinfo", ".metadata.json")
