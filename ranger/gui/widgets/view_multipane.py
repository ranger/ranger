# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

import curses
from ranger.container.settings import SIGNAL_PRIORITY_AFTER_SYNC
from ranger.gui.widgets.view_base import ViewBase
from ranger.gui.widgets.browsercolumn import BrowserColumn


class ViewMultipane(ViewBase):  # pylint: disable=too-many-ancestors

    def __init__(self, win):
        ViewBase.__init__(self, win)

        self.settings.signal_bind('setopt.multipane_orientation', self._layoutchange_handler,
                                  priority=SIGNAL_PRIORITY_AFTER_SYNC)
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

        for child in list(self.container):
            self.remove_child(child)
            child.destroy()
        tab_list = self.fm.get_tab_list()
        for name in tab_list:
            column = BrowserColumn(self.win, 0, tab=self.fm.tabs[name])
            column.display_infostring = True
            if name == self.fm.current_tab:
                self.main_column = column
                # For theming: marked files etc.
                column.main_column = True
            else:
                column.main_column = None
            self.columns.append(column)
            self.add_child(column)
        self.resize(self.y, self.x, self.hei, self.wid)

    def draw(self):
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

    def _draw_borders(self, border_types):
        # Referenced from ranger.gui.widgets.view_miller
        win = self.win
        self.color('in_browser', 'border')
        orientation = self.settings.multipane_orientation
        if orientation is None:
            orientation = 'vertical'

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
                    if orientation != 'vertical':
                        y = child.y + child.hei - 1
                        win.hline(y, 1, curses.ACS_HLINE, self.wid - 2)
                        if 'outline' in border_types:
                            self.addch(y, 0, curses.ACS_LTEE, 0)
                            self.addch(y, self.wid - 1, curses.ACS_RTEE, 0)
                        continue

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

            if orientation == 'vertical':
                start = max(bordered_column.x - 1, 0)
                end = min(start + bordered_column.wid + 1, self.wid - 1)
            else:
                start = max(bordered_column.y - 2, 0)
                end = min(start + bordered_column.hei + 1, self.hei - 1)
            try:
                self._draw_border_rectangle(start, end, orientation=orientation)
            except curses.error:
                pass

    def click(self, event):
        direction = event.mouse_wheel_direction()

        for column in self.columns:
            if event in column:
                if column.tab != self.fm.thistab:
                    for name, tab in self.fm.tabs.items():
                        if tab == column.tab:
                            # input goes to wrong column without this
                            # because browsercolumn uses enter_dir()
                            self.fm.tab_open(name)
                if direction:
                    column.scroll(direction)
                else:
                    column.click(event)

                return True

        return False

    def resize(self, y, x, hei=None, wid=None):  # pylint: disable=too-many-locals
        ViewBase.resize(self, y, x, hei, wid)

        border_type = self._draw_borders_setting()
        if border_type in ['outline', 'both', 'true', 'active-pane']:
            # 'true' for backwards compat., no height pad needed for 'separators'
            pad = 1
        else:
            pad = 0
        left = 0
        top = 0

        vertical = False
        orientation = self.settings.multipane_orientation
        if orientation is None or orientation == 'vertical':
            vertical = True

        total = wid if vertical else hei
        col_count = len(self.columns)
        elem_size = int((total - 2 - (col_count - 1)) / col_count)
        rest = total - (2 + col_count - 1 + col_count * elem_size)
        for column in self.columns:
            this_size = elem_size + (rest > 0)
            rest -= rest > 0
            this_hei = hei - pad * 2 if vertical else max(1, this_size)
            this_wid = max(1, this_size) if vertical else wid - pad * 2
            column.resize(top + pad, left + pad, this_hei, this_wid)
            if vertical:
                left += this_wid + 1
            else:
                top += this_hei + 1

    def poke(self):
        current_tab = self.fm.current_tab
        for name, tab in self.fm.tabs.items():
            if tab.thisdir is None:
                self.fm.tab_open(name)
        if current_tab != self.fm.current_tab:
            self.fm.tab_open(current_tab)

        ViewBase.poke(self)

        if self.old_draw_borders != self._draw_borders_setting():
            self.resize(self.y, self.x, self.hei, self.wid)
            self.old_draw_borders = self._draw_borders_setting()
