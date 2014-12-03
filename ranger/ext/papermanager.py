# Copyright (C) 2014  Roman Zimbelmann <hut@lepus.uberspace.de>
# This software is distributed under the terms of the GNU GPL version 3.

"""
A Paper Manager that reads metadata information about papers from a file.

The file is named .paperinfo and is formatted as comma-separated values.

The columns are:
1. Filename
2. Date
3. Title
4. Authors
5. URL
"""

PAPERINFO_FILE_NAME = ".paperinfo"
DEEP_SEARCH_DEFAULT = True

import csv
from os.path import join, dirname, exists, basename

from ranger.ext.openstruct import OpenStruct

class PaperManager(object):
    def __init__(self):
        self.metadata_cache = dict()
        self.metafile_cache = dict()
        self.deep_search = DEEP_SEARCH_DEFAULT

    def reset(self):
        self.metadata_cache.clear()
        self.metafile_cache.clear()

    def get_paper_info(self, filename):
        try:
            return self.metadata_cache[filename]
        except KeyError:
            result = OpenStruct(filename=filename, title=None, year=None,
                    authors=None, url=None)

            valid = (filename, basename(filename))
            for metafile in self._get_metafile_names(filename):
                for entry in self._get_metafile_content(metafile):
                    if entry[0] in valid:
                        self._fill_ostruct_with_data(result, entry)
                        self.metadata_cache[filename] = result
                        return result

            # Cache the value
            self.metadata_cache[filename] = result
            return result

    def set_paper_info(self, filename, update_dict):
        pass

    def _get_metafile_content(self, metafile):
        if metafile in self.metafile_cache:
            return self.metafile_cache[metafile]
        else:
            if exists(metafile):
                reader = csv.reader(open(metafile, "r"),
                        skipinitialspace=True)

                entries = list(entry for entry in reader if len(entry) == 5)
                self.metafile_cache[metafile] = entries
                return entries
            else:
                return []

    def _get_metafile_names(self, path):
        base = dirname(path)
        yield join(base, PAPERINFO_FILE_NAME)
        if self.deep_search:
            dirs = base.split("/")[1:]
            for i in reversed(range(len(dirs))):
                yield join("/" + "/".join(dirs[0:i]), PAPERINFO_FILE_NAME)

    def _fill_ostruct_with_data(self, ostruct, dataset):
        filename, year, title, authors, url = dataset
        if year:    ostruct.year = year
        if title:   ostruct.title = title
        if authors: ostruct.authors = authors.split(",")
        if url:     ostruct.url = url
