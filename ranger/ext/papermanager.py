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
        result = None
        found = False
        valid = (filename, basename(filename))
        first_metafile = None

        if not self.deep_search:
            metafile = next(self._get_metafile_names(filename))
            return self._set_pager_info_raw(filename, update_dict, metafile)

        for i, metafile in enumerate(self._get_metafile_names(filename)):
            if i == 0:
                first_metafile = metafile

            csvfile = None
            try:
                csvfile = open(metafile, "r")
            except:
                # .paperinfo file doesn't exist... look for another one.
                pass
            else:
                reader = csv.reader(csvfile, skipinitialspace=True)
                for row in reader:
                    name, year, title, authors, url = row
                    if name in valid:
                        return self._set_pager_info_raw(filename, update_dict,
                                metafile)
            finally:
                if csvfile:
                    csvfile.close()

        # No .paperinfo file found, so let's create a new one in the same path
        # as the given file.
        if first_metafile:
            return self._set_pager_info_raw(filename, update_dict, first_metafile)

    def _set_pager_info_raw(self, filename, update_dict, metafile):
        valid = (filename, basename(filename))

        try:
            with open(metafile, "r") as infile:
                reader = csv.reader(infile, skipinitialspace=True)
                rows = list(reader)
        except IOError:
            rows = []

        with open(metafile, "w") as outfile:
            writer = csv.writer(outfile)
            found = False

            # Iterate through all rows and write them back to the file.
            for row in rows:
                if not found and row[0] in valid:
                    # When finding the row that corresponds to the given filename,
                    # update the items with the information from update_dict.
                    self._fill_row_with_ostruct(row, update_dict)
                    found = True
                writer.writerow(row)

            # If the row was never found, create a new one.
            if not found:
                row = [basename(filename), None, None, None, None]
                self._fill_row_with_ostruct(row, update_dict)
                writer.writerow(row)

    def _fill_row_with_ostruct(self, row, update_dict):
        for key, value in update_dict.items():
            if key == "year":
                row[1] = value
            elif key == "title":
                row[2] = value
            elif key == "authors":
                row[3] = value
            elif key == "url":
                row[4] = value

    def _get_metafile_content(self, metafile):
        if metafile in self.metafile_cache:
            return self.metafile_cache[metafile]
        else:
            if exists(metafile):
                reader = csv.reader(open(metafile, "r"), skipinitialspace=True)

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
        if authors: ostruct.authors = authors
        if url:     ostruct.url = url
