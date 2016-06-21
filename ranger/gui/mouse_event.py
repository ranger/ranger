# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

import curses


class MouseEvent(object):
    PRESSED = [0,
            curses.BUTTON1_PRESSED,
            curses.BUTTON2_PRESSED,
            curses.BUTTON3_PRESSED,
            curses.BUTTON4_PRESSED]
    CTRL_SCROLLWHEEL_MULTIPLIER = 5

    def __init__(self, getmouse):
        """Creates a MouseEvent object from the result of win.getmouse()"""
        _, self.x, self.y, _, self.bstate = getmouse

        # x-values above ~220 suddenly became negative, apparently
        # it's sufficient to add 0xFF to fix that error.
        if self.x < 0:
            self.x += 0xFF

        if self.y < 0:
            self.y += 0xFF

    def pressed(self, n):
        """Returns whether the mouse key n is pressed"""
        try:
            return (self.bstate & MouseEvent.PRESSED[n]) != 0
        except Exception:
            return False

    def mouse_wheel_direction(self):
        """Returns the direction of the scroll action, 0 if there was none"""
        # If the bstate > ALL_MOUSE_EVENTS, it's an invalid mouse button.
        # I interpret invalid buttons as "scroll down" because all tested
        # systems have a broken curses implementation and this is a workaround.
        # Recently it seems to have been fixed, as 2**21 was introduced as
        # the code for the "scroll down" button.
        if self.bstate & curses.BUTTON4_PRESSED:
            return self.ctrl() and -self.CTRL_SCROLLWHEEL_MULTIPLIER or -1
        elif self.bstate & curses.BUTTON2_PRESSED \
                or self.bstate & 2**21 \
                or self.bstate > curses.ALL_MOUSE_EVENTS:
            return self.ctrl() and self.CTRL_SCROLLWHEEL_MULTIPLIER or 1
        else:
            return 0

    def ctrl(self):
        return self.bstate & curses.BUTTON_CTRL

    def alt(self):
        return self.bstate & curses.BUTTON_ALT

    def shift(self):
        return self.bstate & curses.BUTTON_SHIFT

    def key_invalid(self):
        return self.bstate > curses.ALL_MOUSE_EVENTS
