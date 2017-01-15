# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""This class provides convenient methods for movement operations.

Direction objects are handled just like dicts but provide
methods like up() and down() which give you the correct value
for the vertical direction, even if only the "up" or "down" key
has been defined.


>>> d = Direction(down=5)
>>> d.down()
5
>>> d.up()
-5
>>> bool(d.horizontal())
False
"""

from __future__ import (absolute_import, print_function)


class Direction(dict):

    def __init__(self, dictionary=None, **keywords):
        if dictionary is not None:
            dict.__init__(self, dictionary)
        else:
            dict.__init__(self, keywords)
        if 'to' in self:
            self['down'] = self['to']
            self['absolute'] = True

    def copy(self):
        return Direction(**self)

    def _get_bool(self, first, second, fallback=None):
        try:
            return self[first]
        except Exception:
            try:
                return not self[second]
            except Exception:
                return fallback

    def _get_direction(self, first, second, fallback=0):
        try:
            return self[first]
        except Exception:
            try:
                return -self[second]
            except Exception:
                return fallback

    def up(self):  # pylint: disable=invalid-name
        return -Direction.down(self)  # pylint: disable=invalid-unary-operand-type

    def down(self):
        return Direction._get_direction(self, 'down', 'up')

    def right(self):
        return Direction._get_direction(self, 'right', 'left')

    def absolute(self):
        return Direction._get_bool(self, 'absolute', 'relative')

    def left(self):
        return -Direction.right(self)  # pylint: disable=invalid-unary-operand-type

    def relative(self):
        return not Direction.absolute(self)

    def vertical_direction(self):
        down = Direction.down(self)
        return (down > 0) - (down < 0)

    def horizontal_direction(self):
        right = Direction.right(self)
        return (right > 0) - (right < 0)

    def vertical(self):
        return set(self) & set(['up', 'down'])

    def horizontal(self):
        return set(self) & set(['left', 'right'])

    def pages(self):
        return 'pages' in self and self['pages']

    def percentage(self):
        return 'percentage' in self and self['percentage']

    def cycle(self):
        return self.get('cycle') in ('true', 'on', 'yes')

    def multiply(self, n):
        for key in ('up', 'right', 'down', 'left'):
            try:
                self[key] *= n
            except Exception:
                pass

    def set(self, n):
        for key in ('up', 'right', 'down', 'left'):
            if key in self:
                self[key] = n

    def move(self, direction, override=None, minimum=0,  # pylint: disable=too-many-arguments
             maximum=9999, current=0, pagesize=1, offset=0):
        """Calculates the new position in a given boundary.

        Example:
        >>> d = Direction(pages=True)
        >>> d.move(direction=3)
        3
        >>> d.move(direction=3, current=2)
        5
        >>> d.move(direction=3, pagesize=5)
        15
        >>> # Note: we start to count at zero.
        >>> d.move(direction=3, pagesize=5, maximum=10)
        9
        >>> d.move(direction=9, override=2)
        18
        """
        pos = direction
        if override is not None:
            if self.absolute():
                pos = override
            else:
                pos *= override
        if self.pages():
            pos *= pagesize
        elif self.percentage():
            pos *= maximum / 100.0
        if self.absolute():
            if pos < minimum:
                pos += maximum
        else:
            pos += current
        if self.cycle():
            return minimum + pos % (maximum + offset - minimum)
        return int(max(min(pos, maximum + offset - 1), minimum))

    def select(self, lst, current, pagesize, override=None, offset=1):
        dest = self.move(direction=self.down(), override=override,
                         current=current, pagesize=pagesize, minimum=0, maximum=len(lst) + 1)
        selection = lst[min(current, dest):max(current, dest) + offset]
        return dest + offset - 1, selection


if __name__ == '__main__':
    import doctest
    doctest.testmod()
