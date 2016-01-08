# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""
A library for abstracting calls to curses

This should replace the low level code in ranger.gui.curses_shortcuts and all
the GUI code in the long run.
"""

import curses
import _curses


def safe_addstr(win, *args):
    y, x = win.getyx()
    try:
        win.addstr(*args)
    except:
        if len(args) > 1:
            win.move(y, x)
            try:
                win.addstr(*_fix_surrogates(args))
            except:
                pass


def safe_addnstr(win, *args):
    y, x = win.getyx()
    try:
        win.addnstr(*args)
    except:
        if len(args) > 2:
            win.move(y, x)
            try:
                win.addnstr(*_fix_surrogates(args))
            except:
                pass


def _fix_surrogates(args):
    return [isinstance(arg, str) and arg.encode('utf-8', 'surrogateescape')
            .decode('utf-8', 'replace') or arg for arg in args]


def draw_lines(win, lines, x, y=0, maxwidth=None, maxheight=None):
    """
    Draw a list of preformatted lines on the given curses window

    <lines> is a list with items in this format:
        [[string, curses_attribute], ...]

    E.g. [[["hello ", 0], ["world", curses.A_BOLD]], [["line 2", 0]]]
    """
    assert x >= 0
    assert y >= 0
    assert maxwidth >= 0
    assert isinstance(lines, list), lines
    assert all(isinstance(line, list) for line in lines), lines

    if y >= maxheight or x >= maxwidth:
        return

    for yoffset, line in enumerate(lines):
        this_y = y + yoffset
        if this_y >= maxheight:
            break
        draw_line(win, line, x, this_y, maxwidth)


def draw_line(win, line, x, y, maxwidth):
    assert x >= 0
    assert y >= 0
    assert maxwidth >= 0
    assert isinstance(line, list), line

    try:
        win.move(y, x)
    except:
        return
    for text, attr in line:
        safe_addnstr(win, text, maxwidth - x, attr)
