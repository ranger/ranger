# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""
A Progress Tracker of any Loadable that manages all the progress
related statistics.
"""

from __future__ import division

import time
from ranger.ext.human_readable import human_readable


class ProgressTracker(object):

    def __init__(self, total_items=0):
        self.total_items = total_items
        self.done = 0
        self.start_time = time.time()

    def step(self, stepsize=1):
        self.done += stepsize

    @property
    def percent(self):
        if self.total_items == 0:
            return 0
        return (self.done / self.total_items) * 100

    @property
    def average_rate(self):
        time_diff = time.time() - self.start_time
        rate = self.done / time_diff
        return rate

    def get_status_text(self):
        raise NotImplementedError('Please Implement this method')


class DirectoryProgressTracker(ProgressTracker):
    def get_status_text(self):
        return '{:3.2f}%'.format(self.percent)


class FileProgressTracker(ProgressTracker):
    def get_status_text(self):
        average_rate = human_readable(self.average_rate, '') + '/s'
        return '{:3.2f}% {:>7}'.format(self.percent, average_rate)
