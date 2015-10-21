# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""The BrowserView manages a set of BrowserColumns."""

import curses, _curses
from ranger.ext.signals import Signal
from ranger.ext.keybinding_parser import key_to_string
from . import Widget
from .browsercolumn import BrowserColumn
from .pager import Pager
from ..displayable import DisplayableContainer

class BrowserView(Widget, DisplayableContainer):
    ratios = None
    preview = True
    is_collapsed = False
    draw_bookmarks = False
    stretch_ratios = None
    need_clear = False
    old_collapse = False
    draw_hints = False
    draw_info = False

    def __init__(self, win, ratios, preview = True):
        DisplayableContainer.__init__(self, win)
        self.preview = preview
        self.columns = []

        self.pager = Pager(self.win, embedded=True)
        self.pager.visible = False
        self.add_child(self.pager)

        self.change_ratios(ratios)

        for option in ('preview_directories', 'preview_files'):
            self.settings.signal_bind('setopt.' + option,
                    self._request_clear_if_has_borders, weak=True)

        self.fm.signal_bind('move', self.request_clear)
        self.settings.signal_bind('setopt.column_ratios', self.request_clear)

        self.old_draw_borders = self.settings.draw_borders

    def change_ratios(self, ratios):
        if isinstance(ratios, Signal):
            ratios = ratios.value

        for column in self.columns:
            column.destroy()
            self.remove_child(column)
        self.columns = []

        ratio_sum = float(sum(ratios))
        self.ratios = tuple(x / ratio_sum for x in ratios)

        last = 0.1 if self.settings.padding_right else 0
        if len(self.ratios) >= 2:
            self.stretch_ratios = self.ratios[:-2] + \
                    ((self.ratios[-2] + self.ratios[-1] * 1.0 - last),
                    (self.ratios[-1] * last))

        offset = 1 - len(ratios)
        if self.preview: offset += 1

        for level in range(len(ratios)):
            fl = BrowserColumn(self.win, level + offset)
            self.add_child(fl)
            self.columns.append(fl)

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
        if self.settings.draw_borders:
            self._draw_borders()
        if self.draw_bookmarks:
            self._draw_bookmarks()
        elif self.draw_hints:
            self._draw_hints()
        elif self.draw_info:
            self._draw_info(self.draw_info)

    def finalize(self):
        if self.pager.visible:
            try:
                self.fm.ui.win.move(self.main_column.y, self.main_column.x)
            except:
                pass
        else:
            try:
                x = self.main_column.x
                y = self.main_column.y + self.main_column.target.pointer\
                        - self.main_column.scroll_begin
                self.fm.ui.win.move(y, x)
            except:
                pass

    def _draw_borders(self):
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
        if self.settings.padding_right and not self.pager.visible and \
                self.is_collapsed:
            right_end = self.columns[-1].x - 1
            if right_end < left_start:
                right_end = self.wid - 1

        # Draw horizontal lines and the leftmost vertical line
        try:
            win.hline(0, left_start, curses.ACS_HLINE, right_end - left_start)
            win.hline(self.hei - 1, left_start, curses.ACS_HLINE,
                    right_end - left_start)
            win.vline(1, left_start, curses.ACS_VLINE, self.hei - 2)
        except _curses.error:
            pass

        # Draw the vertical lines in the middle
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
                win.vline(1, x, curses.ACS_VLINE, y - 1)
                self.addch(0, x, curses.ACS_TTEE, 0)
                self.addch(y, x, curses.ACS_BTEE, 0)
            except:
                # in case it's off the boundaries
                pass

        # Draw the last vertical line
        try:
            win.vline(1, right_end, curses.ACS_VLINE, self.hei - 2)
        except _curses.error:
            pass

        self.addch(0, left_start, curses.ACS_ULCORNER)
        self.addch(self.hei - 1, left_start, curses.ACS_LLCORNER)
        self.addch(0, right_end, curses.ACS_URCORNER)
        self.addch(self.hei - 1, right_end, curses.ACS_LRCORNER)

    def _draw_bookmarks(self):
        self.columns[-1].clear_image(force=True)
        self.fm.bookmarks.update_if_outdated()
        self.color_reset()
        self.need_clear = True

        sorted_bookmarks = sorted((item for item in self.fm.bookmarks \
            if self.fm.settings.show_hidden_bookmarks or \
            '/.' not in item[1].path), key=lambda t: t[0].lower())

        hei = min(self.hei - 1, len(sorted_bookmarks))
        ystart = self.hei - hei

        maxlen = self.wid
        self.addnstr(ystart - 1, 0, "mark  path".ljust(self.wid), self.wid)

        whitespace = " " * maxlen
        for line, items in zip(range(self.hei-1), sorted_bookmarks):
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
        self.need_clear = True
        hints = []
        for k, v in self.fm.ui.keybuffer.pointer.items():
            k = key_to_string(k)
            if isinstance(v, dict):
                text = '...'
            else:
                text = v
            if text.startswith('hint') or text.startswith('chain hint'):
                continue
            hints.append((k, text))
        hints.sort(key=lambda t: t[1])

        hei = min(self.hei - 1, len(hints))
        ystart = self.hei - hei
        self.addnstr(ystart - 1, 0, "key          command".ljust(self.wid),
                self.wid)
        try:
            self.win.chgat(ystart - 1, 0, curses.A_UNDERLINE)
        except:
            pass
        whitespace = " " * self.wid
        i = ystart
        for key, cmd in hints:
            string = " " + key.ljust(11) + " " + cmd
            self.addstr(i, 0, whitespace)
            self.addnstr(i, 0, string, self.wid)
            i += 1

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
                except:
                    return self.old_collapse

        self.old_collapse = result
        return result

    def resize(self, y, x, hei, wid):
        """Resize all the columns according to the given ratio"""
        DisplayableContainer.resize(self, y, x, hei, wid)
        borders = self.settings.draw_borders
        pad = 1 if borders else 0
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
                    self.columns[i].resize(pad, left - 1, hei - pad * 2, 1)
                    self.columns[i].visible = False
                    continue

            if i == last_i - 1:
                self.pager.resize(pad, left, hei - pad * 2, \
                        max(1, self.wid - left - pad))

                if cut_off:
                    self.columns[i].resize(pad, left, hei - pad * 2, \
                            max(1, self.wid - left - pad))
                    continue

            try:
                self.columns[i].resize(pad, left, hei - pad * 2, \
                        max(1, wid - 1))
            except KeyError:
                pass

            left += wid

    def click(self, event):
        if DisplayableContainer.click(self, event):
            return True
        direction = event.mouse_wheel_direction()
        if direction:
            self.main_column.scroll(direction)
        return False

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
        DisplayableContainer.poke(self)

        # Show the preview column when it has a preview but has
        # been hidden (e.g. because of padding_right = False)
        if not self.pager.visible and not self.columns[-1].visible and \
        self.columns[-1].target and self.columns[-1].target.is_directory \
        or self.columns[-1].has_preview() and not self.pager.visible:
            self.columns[-1].visible = True

        if self.preview and self.is_collapsed != self._collapse():
            if self.fm.settings.preview_files:
                # force clearing the image when resizing preview column
                self.columns[-1].clear_image(force=True)
            self.resize(self.y, self.x, self.hei, self.wid)

        if self.old_draw_borders != self.settings.draw_borders:
            self.resize(self.y, self.x, self.hei, self.wid)
            self.old_draw_borders = self.settings.draw_borders
