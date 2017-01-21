# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

from ranger.gui.widgets.view_base import ViewBase
from ranger.gui.widgets.browsercolumn import BrowserColumn


class ViewMultipane(ViewBase):  # pylint: disable=too-many-ancestors

    def __init__(self, win):
        ViewBase.__init__(self, win)

        self.fm.signal_bind('tab.layoutchange', self._layoutchange_handler)
        self.fm.signal_bind('tab.change', self._tabchange_handler)
        self.rebuild()

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

    def resize(self, y, x, hei=None, wid=None):
        ViewBase.resize(self, y, x, hei, wid)
        column_width = int((wid - len(self.columns) + 1) / len(self.columns))
        left = 0
        top = 0
        for column in self.columns:
            column.resize(top, left, hei, max(1, column_width))
            left += column_width + 1
            column.need_redraw = True
        self.need_redraw = True
