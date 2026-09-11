# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""The base GUI element for views on the directory"""

from __future__ import (absolute_import, division, print_function)

import curses
from ranger.container import settings
from ranger.ext.keybinding_parser import key_to_string
from . import Widget
from ..displayable import DisplayableContainer


class BorderGlyphset(  # pylint: disable=too-few-public-methods,too-many-instance-attributes
        object):

    def __init__(  # pylint: disable=invalid-name
            self, glyphstr):
        if glyphstr is None or glyphstr == "":
            # default ACS glyphs: ─│┌┬┐├┼┤└┴┘
            self.HLINE = curses.ACS_HLINE
            self.VLINE = curses.ACS_VLINE
            self.ULCORNER = curses.ACS_ULCORNER
            self.TTEE = curses.ACS_TTEE
            self.URCORNER = curses.ACS_URCORNER
            self.LTEE = curses.ACS_LTEE
            self.PLUS = curses.ACS_PLUS
            self.RTEE = curses.ACS_RTEE
            self.LLCORNER = curses.ACS_LLCORNER
            self.BTEE = curses.ACS_BTEE
            self.LRCORNER = curses.ACS_LRCORNER
        else:
            (
                self.HLINE,
                self.VLINE,
                self.ULCORNER,
                self.TTEE,
                self.URCORNER,
                self.LTEE,
                self.PLUS,
                self.RTEE,
                self.LLCORNER,
                self.BTEE,
                self.LRCORNER,
            ) = glyphstr


class ViewBase(Widget, DisplayableContainer):  # pylint: disable=too-many-instance-attributes
    draw_bookmarks = False
    need_clear = False
    draw_hints = False
    draw_info = False

    def __init__(self, win):  # pylint: disable=super-init-not-called
        DisplayableContainer.__init__(self, win)

        self.fm.signal_bind('move', self.request_clear)
        self.settings.signal_bind('setopt.draw_borders_glyphset', self._reset_glyphset,
                                  priority=settings.SIGNAL_PRIORITY_AFTER_SYNC)
        self.old_draw_borders = self.settings.draw_borders
        self._reset_glyphset()

        self.columns = None
        self.main_column = None
        self.pager = None

    def _reset_glyphset(self):
        self.glyphs = BorderGlyphset(self.settings.draw_borders_glyphset)

    def request_clear(self):
        self.need_clear = True

    def draw(self):
        if self.need_clear:
            self.win.erase()
            self.need_redraw = True
            self.need_clear = False
        for tab in self.fm.tabs.values():
            directory = tab.thisdir
            if directory:
                directory.load_content_if_outdated()
                directory.use()
        DisplayableContainer.draw(self)
        if self.draw_bookmarks:
            self._draw_bookmarks()
        elif self.draw_hints:
            self._draw_hints()
        elif self.draw_info:
            self._draw_info(self.draw_info)

    def finalize(self):
        if self.pager is not None and self.pager.visible:
            try:
                self.fm.ui.win.move(self.main_column.y, self.main_column.x)
            except curses.error:
                pass
        else:
            col_x = self.main_column.x
            col_y = self.main_column.y - self.main_column.scroll_begin
            if self.main_column.target:
                col_y += self.main_column.target.pointer
            try:
                self.fm.ui.win.move(col_y, col_x)
            except curses.error:
                pass

    def _draw_border_rectangle(self, left_start, right_end):
        # Draw border lines
        self.whline(0, left_start + 1, self.glyphs.HLINE, (right_end - left_start - 1))
        self.whline(self.hei - 1, left_start + 1, self.glyphs.HLINE, (right_end - left_start - 1))
        self.wvline(1, left_start, self.glyphs.VLINE, self.hei - 2)
        self.wvline(1, right_end, self.glyphs.VLINE, self.hei - 2)

        # Draw corners
        self.addch(0, left_start, self.glyphs.ULCORNER)
        self.addch(self.hei - 1, left_start, self.glyphs.LLCORNER)
        self.addch(0, right_end, self.glyphs.URCORNER)
        self.addch(self.hei - 1, right_end, self.glyphs.LRCORNER)

    def _draw_bookmarks(self):
        self.columns[-1].clear_image(force=True)
        self.fm.bookmarks.update_if_outdated()
        self.color_reset()
        self.need_clear = True

        sorted_bookmarks = sorted(
            (
                item for item in self.fm.bookmarks
                if self.fm.settings.show_hidden_bookmarks
                or '/.' not in item[1].path
            ),
            key=lambda t: t[0].lower(),
        )

        hei = min(self.hei - 1, len(sorted_bookmarks))
        ystart = self.hei - hei

        maxlen = self.wid
        self.addnstr(ystart - 1, 0, "mark  path".ljust(self.wid), self.wid)

        whitespace = " " * maxlen
        for line, items in zip(range(self.hei - 1), sorted_bookmarks):
            key, mark = items
            string = " " + key + "   " + mark.path
            self.addstr(ystart + line, 0, whitespace)
            self.addnstr(ystart + line, 0, string, self.wid)

        self.win.chgat(ystart - 1, 0, curses.A_UNDERLINE)

    def _draw_info(self, lines):
        hei = min(self.hei - 1, len(lines))
        ystart = self.hei - hei
        i = ystart
        whitespace = " " * self.wid
        for line in lines:
            if i >= self.hei:
                break
            self.addstr(i, 0, whitespace)
            self.addnstr(i, 0, line, self.wid)
            i += 1

    def _draw_hints(self):
        self.columns[-1].clear_image(force=True)
        self.color_reset()
        self.need_clear = True
        hints = []

        def populate_hints(keymap, prefix=""):
            for key, value in keymap.items():
                key = prefix + key_to_string(key)
                if isinstance(value, dict):
                    populate_hints(value, key)
                else:
                    text = value
                    if text.startswith('hint') or text.startswith('chain hint'):
                        continue
                    hints.append((key, text))
        populate_hints(self.fm.ui.keybuffer.pointer)

        def sort_hints(hints):
            """Sort the hints by the action string but first group them by the
            first key.

            """
            from itertools import groupby

            # groupby needs the list to be sorted.
            hints.sort(key=lambda t: t[0])

            def group_hints(hints):
                def first_key(hint):
                    return hint[0][0]

                def action_string(hint):
                    return hint[1]

                return (sorted(group, key=action_string)
                        for _, group
                        in groupby(
                            hints,
                            key=first_key))

            grouped_hints = group_hints(hints)

            # If there are too many hints, collapse the sublists.
            if len(hints) > self.fm.settings.hint_collapse_threshold:
                def first_key_in_group(group):
                    return group[0][0][0]
                grouped_hints = (
                    [(first_key_in_group(hint_group), "...")]
                    if len(hint_group) > 1
                    else hint_group
                    for hint_group in grouped_hints
                )

            # Sort by the first action in group.
            grouped_hints = sorted(grouped_hints, key=lambda g: g[0][1])

            def flatten(nested_list):
                return [item for inner_list in nested_list for item in inner_list]
            return flatten(grouped_hints)
        hints = sort_hints(hints)

        hei = min(self.hei - 1, len(hints))
        ystart = self.hei - hei
        self.addnstr(ystart - 1, 0, "key          command".ljust(self.wid), self.wid)
        try:
            self.win.chgat(ystart - 1, 0, curses.A_UNDERLINE)
        except curses.error:
            pass
        whitespace = " " * self.wid
        i = ystart
        for key, cmd in hints:
            string = " " + key.ljust(11) + " " + cmd
            self.addstr(i, 0, whitespace)
            self.addnstr(i, 0, string, self.wid)
            i += 1

    def click(self, event):
        if DisplayableContainer.click(self, event):
            return True
        direction = event.mouse_wheel_direction()
        if direction:
            self.main_column.scroll(direction)
        return False

    def resize(self, y, x, hei=None, wid=None):
        DisplayableContainer.resize(self, y, x, hei, wid)

    def poke(self):
        DisplayableContainer.poke(self)
