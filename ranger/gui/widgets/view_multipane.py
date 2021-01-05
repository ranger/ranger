# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

import curses
from ranger.gui.widgets.view_base import ViewBase
from ranger.gui.widgets.browsercolumn import BrowserColumn


class ViewMultipane(ViewBase):  # pylint: disable=too-many-ancestors

    def __init__(self, win):
        ViewBase.__init__(self, win)

        self.fm.signal_bind('tab.layoutchange', self._layoutchange_handler)
        self.fm.signal_bind('tab.change', self._tabchange_handler)
        self.rebuild()

        self.old_draw_borders = self._draw_borders_setting()

    def _draw_borders_setting(self):
        # If draw_borders_multipane has not been set, it defaults to `None`
        # and we fallback to using draw_borders. Important to note:
        # `None` is different from the string "none" referring to no borders
        if self.settings.draw_borders_multipane is not None:
            return self.settings.draw_borders_multipane
        else:
            return self.settings.draw_borders

    def _layoutchange_handler(self):
        if self.fm.ui.browser == self:
            self.rebuild()

    def _tabchange_handler(self, signal):
        if self.fm.ui.browser == self:
            if signal.old:
                signal.old.need_redraw = True
            if signal.new:
                signal.new.need_redraw = True

    def rebuild(self):
        self.columns = []

        for child in self.container:
            self.remove_child(child)
            child.destroy()
        for name, tab in self.fm.tabs.items():
            column = BrowserColumn(self.win, 0, tab=tab)
            column.main_column = True
            column.display_infostring = True
            if name == self.fm.current_tab:
                self.main_column = column
            self.columns.append(column)
            self.add_child(column)
        self.resize(self.y, self.x, self.hei, self.wid)

    def draw(self):
        if self.need_clear:
            self.win.erase()
            self.need_redraw = True
            self.need_clear = False

        ViewBase.draw(self)

        if self._draw_borders_setting():
            draw_borders = self._draw_borders_setting()
            if draw_borders in ['both', 'true']:   # 'true' for backwards compat.
                border_types = ['separators', 'outline']
            else:
                border_types = [draw_borders]
            self._draw_borders(border_types)
        if self.draw_bookmarks:
            self._draw_bookmarks()
        elif self.draw_hints:
            self._draw_hints()
        elif self.draw_info:
            self._draw_info(self.draw_info)

    def _draw_border_rectangle(self, left_start, right_end):
        win = self.win
        win.hline(0, left_start, curses.ACS_HLINE, right_end - left_start)
        win.hline(self.hei - 1, left_start, curses.ACS_HLINE, right_end - left_start)
        win.vline(1, left_start, curses.ACS_VLINE, self.hei - 2)
        win.vline(1, right_end, curses.ACS_VLINE, self.hei - 2)
        # Draw the four corners
        self.addch(0, left_start, curses.ACS_ULCORNER)
        self.addch(self.hei - 1, left_start, curses.ACS_LLCORNER)
        self.addch(0, right_end, curses.ACS_URCORNER)
        self.addch(self.hei - 1, right_end, curses.ACS_LRCORNER)

    def _draw_borders(self, border_types):
        # Referenced from ranger.gui.widgets.view_miller
        win = self.win
        self.color('in_browser', 'border')

        left_start = 0
        right_end = self.wid - 1

        # Draw the outline borders
        if 'active-pane' not in border_types:
            if 'outline' in border_types:
                try:
                    self._draw_border_rectangle(left_start, right_end)
                except curses.error:
                    pass

            # Draw the column separators
            if 'separators' in border_types:
                for child in self.columns[:-1]:
                    x = child.x + child.wid
                    y = self.hei - 1
                    try:
                        win.vline(1, x, curses.ACS_VLINE, y - 1)
                        if 'outline' in border_types:
                            self.addch(0, x, curses.ACS_TTEE, 0)
                            self.addch(y, x, curses.ACS_BTEE, 0)
                        else:
                            self.addch(0, x, curses.ACS_VLINE, 0)
                            self.addch(y, x, curses.ACS_VLINE, 0)
                    except curses.error:
                        pass
        else:
            bordered_column = self.main_column
            left_start = max(bordered_column.x, 0)
            right_end = min(left_start + bordered_column.wid, self.wid - 1)
            try:
                self._draw_border_rectangle(left_start, right_end)
            except curses.error:
                pass

    def resize(self, y, x, hei=None, wid=None):
        ViewBase.resize(self, y, x, hei, wid)

        border_type = self._draw_borders_setting()
        if border_type in ['outline', 'both', 'true', 'active-pane']:
            # 'true' for backwards compat., no height pad needed for 'separators'
            pad = 1
        else:
            pad = 0
        column_width = int((wid - len(self.columns) + 1) / len(self.columns))
        left = 0
        top = 0
        for column in self.columns:
            column.resize(top + pad, left, hei - pad * 2, max(1, column_width))
            left += column_width + 1
            column.need_redraw = True
        self.need_redraw = True

    def poke(self):
        ViewBase.poke(self)

        if self.old_draw_borders != self._draw_borders_setting():
            self.resize(self.y, self.x, self.hei, self.wid)
            self.old_draw_borders = self._draw_borders_setting()
