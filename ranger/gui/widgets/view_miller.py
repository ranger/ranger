# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""ViewMiller arranges the view in miller columns"""

from __future__ import (absolute_import, division, print_function)

import curses
from ranger.container import settings
from ranger.gui.widgets.view_base import ViewBase

from .browsercolumn import BrowserColumn
from .pager import Pager
from ..displayable import DisplayableContainer


class ViewMiller(ViewBase):  # pylint: disable=too-many-ancestors,too-many-instance-attributes
    ratios = None
    preview = True
    is_collapsed = False
    stretch_ratios = None
    old_collapse = False

    def __init__(self, win):
        ViewBase.__init__(self, win)
        self.preview = True
        self.columns = []

        self.rebuild()

        for option in ('preview_directories', 'preview_files'):
            self.settings.signal_bind('setopt.' + option,
                                      self._request_clear_if_has_borders, weak=True)

        self.settings.signal_bind('setopt.column_ratios', self.request_clear)
        self.settings.signal_bind('setopt.column_ratios', self.rebuild,
                                  priority=settings.SIGNAL_PRIORITY_AFTER_SYNC)

        self.old_draw_borders = self.settings.draw_borders

    def rebuild(self):
        for child in self.container:
            if isinstance(child, BrowserColumn):
                self.remove_child(child)
                child.destroy()

        self.pager = Pager(self.win, embedded=True)
        self.pager.visible = False
        self.add_child(self.pager)

        ratios = self.settings.column_ratios

        for column in self.columns:
            column.destroy()
            self.remove_child(column)
        self.columns = []

        ratios_sum = sum(ratios)
        self.ratios = tuple((x / ratios_sum) for x in ratios)

        last = 0.1 if self.settings.padding_right else 0
        if len(self.ratios) >= 2:
            self.stretch_ratios = self.ratios[:-2] + \
                ((self.ratios[-2] + self.ratios[-1] * 1.0 - last),
                 (self.ratios[-1] * last))

        offset = 1 - len(ratios)
        if self.preview:
            offset += 1

        for level in range(len(ratios)):
            column = BrowserColumn(self.win, level + offset)
            self.add_child(column)
            self.columns.append(column)

        try:
            self.main_column = self.columns[self.preview and -2 or -1]
        except IndexError:
            self.main_column = None
        else:
            self.main_column.display_infostring = True
            self.main_column.main_column = True

        self.resize(self.y, self.x, self.hei, self.wid)

    def _request_clear_if_has_borders(self):
        if self.settings.draw_borders:
            self.request_clear()

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
        if self.settings.draw_borders:
            draw_borders = self.settings.draw_borders.lower()
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

    def _draw_borders(self, border_types):  # pylint: disable=too-many-branches
        win = self.win

        self.color('in_browser', 'border')

        left_start = 0
        right_end = self.wid - 1

        for child in self.columns:
            if not child.has_preview():
                left_start = child.x + child.wid
            else:
                break

        # Shift the rightmost vertical line to the left to create a padding,
        # but only when padding_right is on, the preview column is collapsed
        # and we did not open the pager to "zoom" in to the file.
        if self.settings.padding_right and not self.pager.visible and self.is_collapsed:
            right_end = self.columns[-1].x - 1
            if right_end < left_start:
                right_end = self.wid - 1

        # Draw horizontal lines and the leftmost vertical line
        if 'outline' in border_types:
            try:
                # pylint: disable=no-member
                win.hline(0, left_start, curses.ACS_HLINE, right_end - left_start)
                win.hline(self.hei - 1, left_start, curses.ACS_HLINE, right_end - left_start)
                win.vline(1, left_start, curses.ACS_VLINE, self.hei - 2)
                # pylint: enable=no-member
            except curses.error:
                pass

        # Draw the vertical lines in the middle
        if 'separators' in border_types:
            for child in self.columns[:-1]:
                if not child.has_preview():
                    continue
                if child.main_column and self.pager.visible:
                    # If we "zoom in" with the pager, we have to
                    # skip the between main_column and pager.
                    break
                x = child.x + child.wid
                y = self.hei - 1
                try:
                    # pylint: disable=no-member
                    win.vline(1, x, curses.ACS_VLINE, y - 1)
                    if 'outline' in border_types:
                        self.addch(0, x, curses.ACS_TTEE, 0)
                        self.addch(y, x, curses.ACS_BTEE, 0)
                    else:
                        self.addch(0, x, curses.ACS_VLINE, 0)
                        self.addch(y, x, curses.ACS_VLINE, 0)
                    # pylint: enable=no-member
                except curses.error:
                    # in case it's off the boundaries
                    pass

        if 'outline' in border_types:
            # Draw the last vertical line
            try:
                # pylint: disable=no-member
                win.vline(1, right_end, curses.ACS_VLINE, self.hei - 2)
                # pylint: enable=no-member
            except curses.error:
                pass

        if 'outline' in border_types:
            # pylint: disable=no-member
            self.addch(0, left_start, curses.ACS_ULCORNER)
            self.addch(self.hei - 1, left_start, curses.ACS_LLCORNER)
            self.addch(0, right_end, curses.ACS_URCORNER)
            self.addch(self.hei - 1, right_end, curses.ACS_LRCORNER)
            # pylint: enable=no-member

    def _collapse(self):
        # Should the last column be cut off? (Because there is no preview)
        if not self.settings.collapse_preview or not self.preview \
                or not self.stretch_ratios:
            return False
        result = not self.columns[-1].has_preview()
        target = self.columns[-1].target
        if not result and target and target.is_file:
            if self.fm.settings.preview_script and \
                    self.fm.settings.use_preview_script:
                try:
                    result = not self.fm.previews[target.realpath]['foundpreview']
                except KeyError:
                    return self.old_collapse

        self.old_collapse = result
        return result

    def resize(self, y, x, hei=None, wid=None):
        """Resize all the columns according to the given ratio"""
        ViewBase.resize(self, y, x, hei, wid)

        border_type = self.settings.draw_borders.lower()
        if border_type in ['outline', 'both', 'true']:
            pad = 1
        else:
            pad = 0
        left = pad
        self.is_collapsed = self._collapse()
        if self.is_collapsed:
            generator = enumerate(self.stretch_ratios)
        else:
            generator = enumerate(self.ratios)

        last_i = len(self.ratios) - 1

        for i, ratio in generator:
            wid = int(ratio * self.wid)

            cut_off = self.is_collapsed and not self.settings.padding_right
            if i == last_i:
                if not cut_off:
                    wid = int(self.wid - left + 1 - pad)
                else:
                    self.columns[i].resize(pad, max(0, left - 1), hei - pad * 2, 1)
                    self.columns[i].visible = False
                    continue

            if i == last_i - 1:
                self.pager.resize(pad, left, hei - pad * 2, max(1, self.wid - left - pad))

                if cut_off:
                    self.columns[i].resize(pad, left, hei - pad * 2, max(1, self.wid - left - pad))
                    continue

            try:
                self.columns[i].resize(pad, left, hei - pad * 2, max(1, wid - 1))
            except KeyError:
                pass

            left += wid

    def open_pager(self):
        self.pager.visible = True
        self.pager.focused = True
        self.need_clear = True
        self.pager.open()
        try:
            self.columns[-1].visible = False
            self.columns[-2].visible = False
        except IndexError:
            pass

    def close_pager(self):
        self.pager.visible = False
        self.pager.focused = False
        self.need_clear = True
        self.pager.close()
        try:
            self.columns[-1].visible = True
            self.columns[-2].visible = True
        except IndexError:
            pass

    def poke(self):
        ViewBase.poke(self)

        # Show the preview column when it has a preview but has
        # been hidden (e.g. because of padding_right = False)
        if not self.columns[-1].visible and self.columns[-1].has_preview() \
                and not self.pager.visible:
            self.columns[-1].visible = True

        if self.preview and self.is_collapsed != self._collapse():
            if self.fm.settings.preview_files:
                # force clearing the image when resizing preview column
                self.columns[-1].clear_image(force=True)
            self.resize(self.y, self.x, self.hei, self.wid)

        if self.old_draw_borders != self.settings.draw_borders:
            self.resize(self.y, self.x, self.hei, self.wid)
            self.old_draw_borders = self.settings.draw_borders
