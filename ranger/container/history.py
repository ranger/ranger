# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

# TODO: rewrite to use deque instead of list

from __future__ import (absolute_import, division, print_function)


class HistoryEmptyException(Exception):
    pass


class History(object):

    def __init__(self, maxlen=None, unique=True):
        assert maxlen is not None, "maxlen cannot be None"
        if isinstance(maxlen, History):
            self.history = list(maxlen.history)
            self.index = maxlen.index
            self.maxlen = maxlen.maxlen
            self.unique = maxlen.unique
        else:
            self.history = []
            self.index = 0
            self.maxlen = maxlen
            self.unique = unique

    def add(self, item):
        # Remove everything after index
        if self.index < len(self.history) - 2:
            del self.history[:self.index + 1]
        # Remove Duplicates
        if self.unique:
            try:
                self.history.remove(item)
            except ValueError:
                pass
        else:
            if self.history and self.history[-1] == item:
                del self.history[-1]
        # Remove first if list is too long
        if len(self.history) > max(self.maxlen - 1, 0):
            del self.history[0]
        # Append the item and fast forward
        self.history.append(item)
        self.index = len(self.history) - 1

    def modify(self, item, unique=False):
        if self.history and unique:
            try:
                self.history.remove(item)
            except ValueError:
                pass
            else:
                self.index -= 1
        try:
            self.history[self.index] = item
        except IndexError:
            self.add(item)

    def rebase(self, other_history):
        """
        Replace the past of this history by that of another.

        This is used when creating a new tab to seamlessly blend in the history
        of the old tab into the new one.

        Example: if self is [a,b,C], the current item is uppercase, and
        other_history is [x,Y,z], then self.merge(other_history) will result in
        [x, y, C].
        """
        assert isinstance(other_history, History)

        if not self.history:
            self.index = 0
            future_length = 0
        else:
            future_length = len(self.history) - self.index - 1

        self.history[:self.index] = list(
            other_history.history[:other_history.index + 1])
        if len(self.history) > self.maxlen:
            self.history = self.history[
                -self.maxlen:]  # pylint: disable=invalid-unary-operand-type

        self.index = len(self.history) - future_length - 1
        assert self.index < len(self.history)

    def __len__(self):
        return len(self.history)

    def current(self):
        if self.history:
            return self.history[self.index]
        else:
            raise HistoryEmptyException

    def top(self):
        try:
            return self.history[-1]
        except IndexError:
            raise HistoryEmptyException

    def bottom(self):
        try:
            return self.history[0]
        except IndexError:
            raise HistoryEmptyException

    def back(self):
        self.index -= 1
        if self.index < 0:
            self.index = 0
        return self.current()

    def move(self, n):
        self.index += n
        if self.index > len(self.history) - 1:
            self.index = len(self.history) - 1
        if self.index < 0:
            self.index = 0
        return self.current()

    def search(self, string, n):
        if n != 0 and string:
            step = 1 if n > 0 else -1
            i = self.index
            steps_left = steps_left_at_start = int(abs(n))
            while steps_left:
                i += step
                if i >= len(self.history) or i < 0:
                    break
                if self.history[i].startswith(string):
                    steps_left -= 1
            if steps_left != steps_left_at_start:
                self.index = i
        return self.current()

    def __iter__(self):
        return self.history.__iter__()

    def forward(self):
        if self.history:
            self.index += 1
            if self.index > len(self.history) - 1:
                self.index = len(self.history) - 1
        else:
            self.index = 0
        return self.current()

    def fast_forward(self):
        if self.history:
            self.index = len(self.history) - 1
        else:
            self.index = 0
