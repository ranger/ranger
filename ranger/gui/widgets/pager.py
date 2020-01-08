# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""The pager displays text and allows you to scroll inside it."""

from __future__ import (absolute_import, division, print_function)

import curses
import logging

from ranger.gui import ansi
from ranger.ext.direction import Direction
from ranger.ext.img_display import ImgDisplayUnsupportedException

from . import Widget


LOG = logging.getLogger(__name__)


# TODO: Scrolling in embedded pager
class Pager(Widget):  # pylint: disable=too-many-instance-attributes
    source = None
    source_is_stream = False

    old_source = None
    old_scroll_begin = 0
    old_startx = 0
    need_clear_image = False
    need_redraw_image = False
    max_width = None

    def __init__(self, win, embedded=False):
        Widget.__init__(self, win)
        self.embedded = embedded
        self.scroll_begin = 0
        self.scroll_extra = 0
        self.startx = 0
        self.markup = None
        self.lines = []
        self.image = None
        self.image_drawn = False

    def _close_source(self):
        if self.source and self.source_is_stream:
            try:
                self.source.close()
            except OSError as ex:
                LOG.error('Unable to close pager source')
                LOG.exception(ex)

    def open(self):
        self.scroll_begin = 0
        self.markup = None
        self.max_width = 0
        self.startx = 0
        self.need_redraw = True

    def clear_image(self, force=False):
        if (force or self.need_clear_image) and self.image_drawn:
            self.fm.image_displayer.clear(self.x, self.y, self.wid, self.hei)
            self.need_clear_image = False
            self.image_drawn = False

    def close(self):
        if self.image:
            self.need_clear_image = True
            self.clear_image()
        self._close_source()

    def destroy(self):
        self.clear_image(force=True)
        Widget.destroy(self)

    def finalize(self):
        self.fm.ui.win.move(self.y, self.x)

    def scrollbit(self, lines):
        target_scroll = self.scroll_extra + lines
        max_scroll = len(self.lines) - self.hei
        self.scroll_extra = max(0, min(target_scroll, max_scroll))
        self.need_redraw = True

    def draw(self):
        if self.need_clear_image:
            self.need_redraw = True

        if self.old_source != self.source:
            self.old_source = self.source
            self.need_redraw = True

        if self.old_scroll_begin != self.scroll_begin or \
                self.old_startx != self.startx:
            self.old_startx = self.startx
            self.old_scroll_begin = self.scroll_begin
            self.need_redraw = True

        if self.need_redraw:
            self.win.erase()
            self.need_redraw_image = True
            self.clear_image()

            if not self.image:
                scroll_pos = self.scroll_begin + self.scroll_extra
                line_gen = self._generate_lines(
                    starty=scroll_pos, startx=self.startx)

                for line, i in zip(line_gen, range(self.hei)):
                    self._draw_line(i, line)

            self.need_redraw = False

    def draw_image(self):
        if self.image and self.need_redraw_image:
            self.source = None
            self.need_redraw_image = False
            try:
                self.fm.image_displayer.draw(self.image, self.x, self.y,
                                             self.wid, self.hei)
            except ImgDisplayUnsupportedException as ex:
                self.fm.settings.preview_images = False
                self.fm.notify(ex, bad=True)
            except Exception as ex:  # pylint: disable=broad-except
                self.fm.notify(ex, bad=True)
            else:
                self.image_drawn = True

    def _draw_line(self, i, line):
        if self.markup is None:
            self.addstr(i, 0, line)
        elif self.markup == 'ansi':
            try:
                self.win.move(i, 0)
            except curses.error:
                pass
            else:
                for chunk in ansi.text_with_fg_bg_attr(line):
                    if isinstance(chunk, tuple):
                        self.set_fg_bg_attr(*chunk)
                    else:
                        self.addstr(chunk)

    def move(self, narg=None, **kw):
        direction = Direction(kw)
        if direction.horizontal():
            self.startx = direction.move(
                direction=direction.right(),
                override=narg,
                maximum=self.max_width,
                current=self.startx,
                pagesize=self.wid,
                offset=-self.wid + 1)
        if direction.vertical():
            movement = dict(
                direction=direction.down(),
                override=narg,
                current=self.scroll_begin,
                pagesize=self.hei,
                offset=-self.hei + 1)
            if self.source_is_stream:
                # For streams, we first pretend that the content ends much later,
                # in case there are still unread lines.
                desired_position = direction.move(
                    maximum=len(self.lines) + 9999,
                    **movement)
                # Then, read the new lines as needed to produce a more accurate
                # maximum for the movement:
                self._get_line(desired_position + self.hei)
            self.scroll_begin = direction.move(
                maximum=len(self.lines),
                **movement)

    def press(self, key):
        self.fm.ui.keymaps.use_keymap('pager')
        self.fm.ui.press(key)

    def set_image(self, image):
        if self.image:
            self.need_clear_image = True
        self.image = image
        self._close_source()
        self.source = None
        self.source_is_stream = False

    def set_source(self, source, strip=False):
        if self.image:
            self.image = None
            self.need_clear_image = True
        self._close_source()

        self.max_width = 0
        if isinstance(source, str):
            self.source_is_stream = False
            self.lines = source.splitlines()
            if self.lines:
                self.max_width = max(len(line) for line in self.lines)
        elif hasattr(source, '__getitem__'):
            self.source_is_stream = False
            self.lines = source
            if self.lines:
                self.max_width = max(len(line) for line in source)
        elif hasattr(source, 'readline'):
            self.source_is_stream = True
            self.lines = []
        else:
            self.source = None
            self.source_is_stream = False
            return False
        self.markup = 'ansi'

        if not self.source_is_stream and strip:
            self.lines = [line.strip() for line in self.lines]

        self.source = source
        return True

    def click(self, event):
        n = 1 if event.ctrl() else 3
        direction = event.mouse_wheel_direction()
        if direction:
            self.move(down=direction * n)
        return True

    def _get_line(self, n, attempt_to_read=True):
        assert isinstance(n, int), n
        try:
            return self.lines[n]
        except (KeyError, IndexError):
            if attempt_to_read and self.source_is_stream:
                try:
                    for line in self.source:
                        if len(line) > self.max_width:
                            self.max_width = len(line)
                        self.lines.append(line)
                        if len(self.lines) > n:
                            break
                except (UnicodeError, IOError):
                    pass
                return self._get_line(n, attempt_to_read=False)
            return ""

    def _generate_lines(self, starty, startx):
        i = starty
        if not self.source:
            return
        while True:
            try:
                line = self._get_line(i).expandtabs(4)
                for part in ((0,) if not
                             self.fm.settings.wrap_plaintext_previews else
                             range(max(1, ((len(line) - 1) // self.wid) + 1))):
                    shift = part * self.wid
                    if self.markup == 'ansi':
                        line_bit = (ansi.char_slice(line, startx + shift,
                                                    self.wid + shift)
                                    + ansi.reset)
                    else:
                        line_bit = line[startx + shift:self.wid + startx
                                        + shift]
                    yield line_bit.rstrip().replace('\r\n', '\n')
            except IndexError:
                return
            i += 1
