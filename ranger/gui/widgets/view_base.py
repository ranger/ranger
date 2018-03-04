# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""The base GUI element for views on the directory"""

from __future__ import (absolute_import, division, print_function)

import curses
from ranger.ext.keybinding_parser import key_to_string
from . import Widget
from ..displayable import DisplayableContainer


class ViewBase(Widget, DisplayableContainer):  # pylint: disable=too-many-instance-attributes
    draw_bookmarks = False
    need_clear = False
    draw_hints = False
    draw_info = False

    def __init__(self, win):  # pylint: disable=super-init-not-called
        DisplayableContainer.__init__(self, win)

        self.fm.signal_bind('move', self.request_clear)
        self.old_draw_borders = self.settings.draw_borders

        self.columns = None
        self.main_column = None
        self.pager = None

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
            col_y = self.main_column.y + self.main_column.target.pointer \
                - self.main_column.scroll_begin
            try:
                self.fm.ui.win.move(col_y, col_x)
            except curses.error:
                pass

    def _draw_bookmarks(self):
        self.columns[-1].clear_image(force=True)
        self.fm.bookmarks.update_if_outdated()
        self.color_reset()
        self.need_clear = True

        sorted_bookmarks = sorted(
            (
                item for item in self.fm.bookmarks
                if self.fm.settings.show_hidden_bookmarks or
                '/.' not in item[1].path
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
        self.columns[-1].clear_image(force=True)
        self.need_clear = True
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
