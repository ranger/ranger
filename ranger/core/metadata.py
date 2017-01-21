# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""
A Metadata Manager that reads information about files from a json database.

The database is contained in a local .metadata.json file.
"""

# TODO: Better error handling if a json file can't be decoded
# TODO: Update metadata keys if a file gets renamed/moved
# TODO: A global metadata file, maybe as a replacement for tags

from __future__ import (absolute_import, division, print_function)

import copy
from os.path import join, dirname, exists, basename
from ranger.ext.openstruct import DefaultOpenStruct as ostruct


METADATA_FILE_NAME = ".metadata.json"
DEEP_SEARCH_DEFAULT = False


class MetadataManager(object):

    def __init__(self):
        # metadata_cache maps filenames to dicts containing their metadata
        self.metadata_cache = dict()
        # metafile_cache maps .metadata.json filenames to their entries
        self.metafile_cache = dict()
        self.deep_search = DEEP_SEARCH_DEFAULT

    def reset(self):
        self.metadata_cache.clear()
        self.metafile_cache.clear()

    def get_metadata(self, filename):
        try:
            return ostruct(copy.deepcopy(self.metadata_cache[filename]))
        except KeyError:
            try:
                return ostruct(copy.deepcopy(self._get_entry(filename)))
            except KeyError:
                return ostruct()

    def set_metadata(self, filename, update_dict):
        if not self.deep_search:
            metafile = next(self._get_metafile_names(filename))
            return self._set_metadata_raw(filename, update_dict, metafile)

        metafile = self._get_metafile_name(filename)
        return self._set_metadata_raw(filename, update_dict, metafile)

    def _set_metadata_raw(self, filename, update_dict, metafile):
        import json

        entries = self._get_metafile_content(metafile)
        try:
            entry = entries[filename]
        except KeyError:
            try:
                entry = entries[basename(filename)]
            except KeyError:
                entry = entries[basename(filename)] = {}
        entry.update(update_dict)

        # Delete key if the value is empty
        for key, value in update_dict.items():
            if value == "":
                del entry[key]

        # If file's metadata become empty after an update, remove it entirely
        if entry == {}:
            try:
                del entries[filename]
            except KeyError:
                try:
                    del entries[basename(filename)]
                except KeyError:
                    pass

        # Full update of the cache, to be on the safe side:
        self.metadata_cache[filename] = entry
        self.metafile_cache[metafile] = entries

        with open(metafile, "w") as fobj:
            json.dump(entries, fobj, check_circular=True, indent=2)

    def _get_entry(self, filename):
        if filename in self.metadata_cache:
            return self.metadata_cache[filename]
        else:

            # Try to find an entry for this file in any of
            # the applicable .metadata.json files
            for metafile in self._get_metafile_names(filename):
                entries = self._get_metafile_content(metafile)
                # Check for a direct match:
                if filename in entries:
                    entry = entries[filename]
                # Check for a match of the base name:
                elif basename(filename) in entries:
                    entry = entries[basename(filename)]
                else:
                    # No match found, try another entry
                    continue

                self.metadata_cache[filename] = entry
                return entry

            raise KeyError

    def _get_metafile_content(self, metafile):
        import json

        if metafile in self.metafile_cache:
            return self.metafile_cache[metafile]

        if exists(metafile):
            with open(metafile, "r") as fobj:
                try:
                    entries = json.load(fobj)
                except ValueError:
                    raise ValueError("Failed decoding JSON file %s" % metafile)
            self.metafile_cache[metafile] = entries
            return entries

        return {}

    def _get_metafile_names(self, path):
        # Iterates through the paths of all .metadata.json files that could
        # influence the metadata of the given file.
        # When deep_search is deactivated, this only yields the .metadata.json
        # file in the same directory as the given file.

        base = dirname(path)
        yield join(base, METADATA_FILE_NAME)
        if self.deep_search:
            dirs = base.split("/")[1:]
            for i in reversed(range(len(dirs))):
                yield join("/" + "/".join(dirs[0:i]), METADATA_FILE_NAME)

    def _get_metafile_name(self, filename):
        first = None
        for metafile in self._get_metafile_names(filename):
            if first is None:
                first = metafile

            entries = self._get_metafile_content(metafile)
            if filename in entries or basename(filename) in entries:
                return metafile

        # _get_metafile_names should return >0 names, but just in case...:
        assert first is not None, "failed finding location for .metadata.json"
        return first
