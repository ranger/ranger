# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""ViewTree arranges the view in a tree"""

from __future__ import (absolute_import, division, print_function)

import curses
from ranger.container import settings
from ranger.gui.widgets.view_base import ViewBase

from .browsercolumn import BrowserColumn
from .pager import Pager
from ..displayable import DisplayableContainer 

class ViewTree(ViewBase):
    # TODO override BrowserColumn to display in tree style
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
        focused_tab = self.fm.tabs[self.fm.current_tab] 

        for child in self.container:
            self.remove_child(child)
            child.destroy()

        self.pager = Pager(self.win, embedded=True)
        self.pager.visible = False
        self.add_child(self.pager)
        
        column = BrowserColumn(self.win, 0, tab=focused_tab)
        column.main_column = True

        column.display_infostring = True
        preview = BrowserColumn(self.win, 1, tab=focused_tab)
        column.display_infostring = True
        self.main_column = column
        self.columns.append(column)
        self.columns.append(preview)
        self.add_child(column)
        self.add_child(preview) 
        
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