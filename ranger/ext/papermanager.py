# Copyright (C) 2014  Roman Zimbelmann <hut@lepus.uberspace.de>
# This software is distributed under the terms of the GNU GPL version 3.

import csv
from os.path import join, dirname, exists, basename

from ranger.ext.openstruct import OpenStruct

class PaperManager(object):
    def __init__(self):
        self.metadata_cache = dict()
        self.metafile_cache = dict()

    def reset(self):
        self.metadata_cache.clear()
        self.metafile_cache.clear()

    def get_paper_info(self, filename):
        try:
            return self.metadata_cache[filename]
        except KeyError:
            result = OpenStruct(title=None, year=None, filename=filename)
            metafile = join(dirname(filename), ".paperinfo")

            # get entries of the metadata file
            if metafile in self.metafile_cache:
                entries = self.metafile_cache[metafile]
            else:
                if exists(metafile):
                    reader = csv.reader(open(metafile, "r"),
                            skipinitialspace=True)

                    entries = list(entry for entry in reader if len(entry) == 3)
                    self.metafile_cache[metafile] = entries
                else:
                    # No metadata file
                    entries = []

            # Find the relevant entry in the metadata file
            valid = (filename, basename(filename))
            for entry in entries:
                if entry[0] in valid:
                    self._fill_ostruct_with_data(result, entry)
                    break

            # Cache the value
            self.metadata_cache[filename] = result
            return result

    def _fill_ostruct_with_data(self, ostruct, dataset):
        filename, year, title = dataset
        if year:
            ostruct.year = year
        if title:
            ostruct.title = title
