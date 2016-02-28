# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

# TODO: rewrite to use deque instead of list

class HistoryEmptyException(Exception):
    pass

class History(object):
    def __init__(self, maxlen=None, unique=True):
        assert maxlen is not None, "maxlen cannot be None"
        if isinstance(maxlen, History):
            self._history = list(maxlen._history)
            self._index = maxlen._index
            self.maxlen = maxlen.maxlen
            self.unique = maxlen.unique
        else:
            self._history = []
            self._index = 0
            self.maxlen = maxlen
            self.unique = unique

    def add(self, item):
        # Remove everything after index
        if self._index < len(self._history) - 2:
            del self._history[:self._index+1]
        # Remove Duplicates
        if self.unique:
            try:
                self._history.remove(item)
            except:
                pass
        else:
            if self._history and self._history[-1] == item:
                del self._history[-1]
        # Remove first if list is too long
        if len(self._history) > max(self.maxlen - 1, 0):
            del self._history[0]
        # Append the item and fast forward
        self._history.append(item)
        self._index = len(self._history) - 1

    def modify(self, item, unique=False):
        if self._history and unique:
            try:
                self._history.remove(item)
                self._index -= 1
            except:
                pass
        try:
            self._history[self._index] = item
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

        if len(self._history) == 0:
            self._index = 0
            future_length = 0
        else:
            future_length = len(self._history) - self._index - 1

        self._history[:self._index] = list(
                other_history._history[:other_history._index + 1])
        if len(self._history) > self.maxlen:
            self._history = self._history[-self.maxlen:]

        self._index = len(self._history) - future_length - 1
        assert self._index < len(self._history)

    def __len__(self):
        return len(self._history)

    def current(self):
        if self._history:
            return self._history[self._index]
        else:
            raise HistoryEmptyException

    def top(self):
        try:
            return self._history[-1]
        except IndexError:
            raise HistoryEmptyException()

    def bottom(self):
        try:
            return self._history[0]
        except IndexError:
            raise HistoryEmptyException()

    def back(self):
        self._index -= 1
        if self._index < 0:
            self._index = 0
        return self.current()

    def move(self, n):
        self._index += n
        if self._index > len(self._history) - 1:
            self._index = len(self._history) - 1
        if self._index < 0:
            self._index = 0
        return self.current()

    def search(self, string, n):
        if n != 0 and string:
            step = n > 0 and 1 or -1
            i = self._index
            steps_left = steps_left_at_start = int(abs(n))
            while steps_left:
                i += step
                if i >= len(self._history) or i < 0:
                    break
                if self._history[i].startswith(string):
                    steps_left -= 1
            if steps_left != steps_left_at_start:
                self._index = i
        return self.current()

    def __iter__(self):
        return self._history.__iter__()

    def forward(self):
        if self._history:
            self._index += 1
            if self._index > len(self._history) - 1:
                self._index = len(self._history) - 1
        else:
            self._index = 0
        return self.current()

    def fast_forward(self):
        if self._history:
            self._index = len(self._history) - 1
        else:
            self._index = 0
