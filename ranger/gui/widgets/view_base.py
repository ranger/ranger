# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""The base GUI element for views on the directory"""

import curses, _curses
from ranger.ext.keybinding_parser import key_to_string
from . import Widget
from ..displayable import DisplayableContainer

class ViewBase(Widget, DisplayableContainer):
    draw_bookmarks = False
    need_clear = False
    draw_hints = False
    draw_info = False

    def __init__(self, win):
        DisplayableContainer.__init__(self, win)

        self.fm.signal_bind('move', self.request_clear)
        self.old_draw_borders = self.settings.draw_borders

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
        if hasattr(self, 'pager') and self.pager.visible:
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

    def click(self, event):
        if DisplayableContainer.click(self, event):
            return True
        direction = event.mouse_wheel_direction()
        if direction:
            self.main_column.scroll(direction)
        return False

    def resize(self, y, x, hei, wid):
        DisplayableContainer.resize(self, y, x, hei, wid)

    def poke(self):
        DisplayableContainer.poke(self)
