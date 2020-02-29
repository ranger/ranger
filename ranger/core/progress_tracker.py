# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""
A Progress Tracker of any Loadable that manages all the progress
related statistics.

Currently, only percent reporting is implemented.
"""

from __future__ import division


class ProgressTracker(object):

    def __init__(self, total_items=0):
        self.total_items = total_items
        self.done = 0

    def step(self, stepsize=1):
        self.done += stepsize

    @property
    def percent(self):
        if self.total_items == 0:
            return 0
        return (self.done / self.total_items) * 100

    def get_status_text(self):
        raise NotImplementedError('Please Implement this method')


class DirectoryProgressTracker(ProgressTracker):
    def get_status_text(self):
        return '{:3.2f}%'.format(self.percent)


class FileProgressTracker(ProgressTracker):
    def get_status_text(self):
        return '{:3.2f}%'.format(self.percent)
