# -*- coding: utf-8 -*-
# Copyright (C) 2009-2013  Roman Zimbelmann <hut@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

"""The BrowserColumn widget displays the contents of a directory or file."""

import curses
import stat
from time import time

from . import Widget
from .pager import Pager
from ranger.ext.widestring import WideString

from ranger.gui.color import *

class BrowserColumn(Pager):
    main_column = False
    display_infostring = False
    display_vcsstate   = True
    scroll_begin = 0
    target = None
    last_redraw_time = -1
    ellipsis = { False: '~', True: '…' }

    old_dir = None
    old_thisfile = None

    def __init__(self, win, level):
        """Initializes a Browser Column Widget

        win = the curses window object of the BrowserView
        level = what to display?

        level >0 => previews
        level 0 => current file/directory
        level <0 => parent directories
        """
        Pager.__init__(self, win)
        Widget.__init__(self, win)
        self.level = level
        self.original_level = level

        self.settings.signal_bind('setopt.display_size_in_main_column',
                self.request_redraw, weak=True)

    def request_redraw(self):
        self.need_redraw = True

    def resize(self, y, x, hei, wid):
        Widget.resize(self, y, x, hei, wid)

    def click(self, event):
        """Handle a MouseEvent"""
        direction = event.mouse_wheel_direction()
        if not (event.pressed(1) or event.pressed(3) or direction):
            return False

        if self.target is None:
            pass

        elif self.target.is_directory:
            if self.target.accessible and self.target.content_loaded:
                index = self.scroll_begin + event.y - self.y

                if direction:
                    if self.level == -1:
                        self.fm.move_parent(direction)
                    else:
                        return False
                elif event.pressed(1):
                    if not self.main_column:
                        self.fm.enter_dir(self.target.path)

                    if index < len(self.target):
                        self.fm.move(to=index)
                elif event.pressed(3):
                    try:
                        clicked_file = self.target.files[index]
                        if clicked_file.is_directory:
                            self.fm.enter_dir(clicked_file.path)
                        elif self.level == 0:
                            self.fm.thisdir.move_to_obj(clicked_file)
                            self.fm.execute_file(clicked_file)
                    except:
                        pass

        else:
            if self.level > 0 and not direction:
                self.fm.move(right=0)

        return True

    def execute_curses_batch(self, line, commands):
        """Executes a list of "commands" which can be easily cached.

        "commands" is a list of lists.    Each element contains
        a text and an attribute.  First, the attribute will be
        set with attrset, then the text is printed.

        Example:
        execute_curses_batch(0, [["hello ", 0], ["world", curses.A_BOLD]])
        """
        try:
            self.win.move(line, 0)
        except:
            return
        for entry in commands:
            text, attr = entry
            self.addstr(text, attr)

    def has_preview(self):
        if self.target is None:
            return False

        if self.target.is_file:
            if not self.target.has_preview():
                return False

        if self.target.is_directory:
            if self.level > 0 and not self.settings.preview_directories:
                return False

        return True

    def level_shift(self, amount):
        self.level = self.original_level + amount

    def level_restore(self):
        self.level = self.original_level

    def poke(self):
        Widget.poke(self)
        self.target = self.fm.thistab.at_level(self.level)

    def draw(self):
        """Call either _draw_file() or _draw_directory()"""
        if self.target != self.old_dir:
            self.need_redraw = True
            self.old_dir = self.target

        if self.target:     # don't garbage collect this directory please
            self.target.use()

        if self.target and self.target.is_directory \
                and (self.level <= 0 or self.settings.preview_directories):
            if self.target.pointed_obj != self.old_thisfile:
                self.need_redraw = True
                self.old_thisfile = self.target.pointed_obj

            if self.target.load_content_if_outdated() \
            or self.target.sort_if_outdated() \
            or self.last_redraw_time < self.target.last_update_time:
                self.need_redraw = True

        if self.need_redraw:
            self.win.erase()
            if self.target is None:
                pass
            elif self.target.is_file:
                Pager.open(self)
                self._draw_file()
            elif self.target.is_directory:
                self._draw_directory()
                Widget.draw(self)
            self.need_redraw = False
            self.last_redraw_time = time()

    def _draw_file(self):
        """Draw a preview of the file, if the settings allow it"""
        self.win.move(0, 0)
        if not self.target.accessible:
            self.addnstr("not accessible", self.wid)
            Pager.close(self)
            return

        if self.target is None or not self.target.has_preview():
            Pager.close(self)
            return

        if self.fm.settings.preview_images and self.target.image:
            self.set_image(self.target.realpath)
            Pager.draw(self)
        else:
            f = self.target.get_preview_source(self.wid, self.hei)
            if f is None:
                Pager.close(self)
            else:
                self.set_source(f)
                Pager.draw(self)

    def _draw_directory(self):
        """Draw the contents of a directory"""
        if self.image:
            self.image = None
            self.need_clear_image = True
            Pager.clear_image(self)

        if self.level > 0 and not self.settings.preview_directories:
            return

        base_color = ['in_browser']

        self.win.move(0, 0)

        if not self.target.content_loaded:
            self.color(tuple(base_color))
            self.addnstr("...", self.wid)
            self.color_reset()
            return

        if self.main_column:
            base_color.append('main_column')

        if not self.target.accessible:
            self.color(tuple(base_color + ['error']))
            self.addnstr("not accessible", self.wid)
            self.color_reset()
            return

        if self.target.empty():
            self.color(tuple(base_color + ['empty']))
            self.addnstr("empty", self.wid)
            self.color_reset()
            return

        self._set_scroll_begin()

        copied = [f.path for f in self.fm.copy_buffer]

        selected_i = self.target.pointer
        for line in range(self.hei):
            i = line + self.scroll_begin
            if line > self.hei:
                break

            try:
                drawn = self.target.files[i]
            except IndexError:
                break

            tagged = self.fm.tags and drawn.realpath in self.fm.tags
            if tagged:
                tagged_marker = self.fm.tags.marker(drawn.realpath)
            else:
                tagged_marker = " "

            key = (self.wid, selected_i == i, drawn.marked, self.main_column,
                    drawn.path in copied, tagged_marker, drawn.infostring,
                    drawn.vcsfilestatus, drawn.vcsremotestatus, self.fm.do_cut)

            if key in drawn.display_data:
                self.execute_curses_batch(line, drawn.display_data[key])
                self.color_reset()
                continue

            text = drawn.basename
            if drawn.marked and (self.main_column or \
                    self.settings.display_tags_in_all_columns):
                text = " " + text

            # Computing predisplay data. predisplay contains a list of lists
            # [string, colorlst] where string is a piece of string to display,
            # and colorlst a list of contexts that we later pass to the
            # colorscheme, to compute the curses attribute.
            predisplay_left = []
            predisplay_right = []
            space = self.wid

            # selection mark
            tagmark = self._draw_tagged_display(tagged, tagged_marker)
            tagmarklen = self._total_len(tagmark)
            if space - tagmarklen > 2:
                predisplay_left += tagmark
                space -= tagmarklen

            # vcs data
            vcsstring = self._draw_vcsstring_display(drawn)
            vcsstringlen = self._total_len(vcsstring)
            if space - vcsstringlen > 2:
                predisplay_right += vcsstring
                space -= vcsstringlen

            # info string
            infostring = self._draw_infostring_display(drawn, space)
            infostringlen = self._total_len(infostring)
            if space - infostringlen > 2:
                predisplay_right = infostring + predisplay_right
                space -= infostringlen

            textstring = self._draw_text_display(text, space)
            textstringlen = self._total_len(textstring)
            predisplay_left += textstring
            space -= textstringlen

            if space > 0:
                predisplay_left.append([' ' * space, []])
            elif space < 0:
                raise Exception("Error: there is not enough space to write "
                        "the text. I have computed spaces wrong.")

            # Computing display data. Now we compute the display_data list
            # ready to display in curses. It is a list of lists [string, attr]

            this_color = base_color + list(drawn.mimetype_tuple) + \
                    self._draw_directory_color(i, drawn, copied)
            display_data = []
            drawn.display_data[key] = display_data

            predisplay = predisplay_left + predisplay_right
            for txt, color in predisplay:
                attr = self.settings.colorscheme.get_attr(*(this_color + color))
                display_data.append([txt, attr])

            self.execute_curses_batch(line, display_data)
            self.color_reset()

    def _total_len(self, predisplay):
        return sum([len(WideString(s)) for s, L in predisplay])

    def _draw_text_display(self, text, space):
        wtext = WideString(text)
        wellip = WideString(self.ellipsis[self.settings.unicode_ellipsis])
        if len(wtext) > space:
            wtext = wtext[:max(0, space - len(wellip))] + wellip

        return [[str(wtext), []]]

    def _draw_tagged_display(self, tagged, tagged_marker):
        tagged_display = []
        if (self.main_column or self.settings.display_tags_in_all_columns) \
                and self.wid > 2:
            if tagged:
                tagged_display.append([tagged_marker, ['tag_marker']])
            else:
                tagged_display.append([" ", ['tag_marker']])
        return tagged_display

    def _draw_infostring_display(self, drawn, space):
        infostring_display = []
        if self.display_infostring and drawn.infostring \
                and self.settings.display_size_in_main_column:
            infostring = str(drawn.infostring) + " "
            if len(infostring) <= space:
                infostring_display.append([infostring, ['infostring']])
        return infostring_display

    def _draw_vcsstring_display(self, drawn):
        vcsstring_display = []
        if self.settings.vcs_aware and (drawn.vcsfilestatus or \
                drawn.vcsremotestatus):
            if drawn.vcsfilestatus:
                vcsstr, vcscol = self.vcsfilestatus_symb[drawn.vcsfilestatus]
            else:
                vcsstr = " "
                vcscol = []
            vcsstring_display.append([vcsstr, ['vcsfile'] + vcscol])

            if drawn.vcsremotestatus:
                vcsstr, vcscol = self.vcsremotestatus_symb[
                        drawn.vcsremotestatus]
            else:

                vcsstr = " "
                vcscol = []
            vcsstring_display.append([vcsstr, ['vcsremote'] + vcscol])
        elif self.target.has_vcschild:
            vcsstring_display.append(["  ", []])
        return vcsstring_display

    def _draw_directory_color(self, i, drawn, copied):
        this_color = []
        if i == self.target.pointer:
            this_color.append('selected')

        if drawn.marked:
            this_color.append('marked')

        if self.fm.tags and drawn.realpath in self.fm.tags:
            this_color.append('tagged')

        if drawn.is_directory:
            this_color.append('directory')
        else:
            this_color.append('file')

        if drawn.stat:
            mode = drawn.stat.st_mode
            if mode & stat.S_IXUSR:
                this_color.append('executable')
            if stat.S_ISFIFO(mode):
                this_color.append('fifo')
            if stat.S_ISSOCK(mode):
                this_color.append('socket')
            if drawn.is_device:
                this_color.append('device')

        if drawn.path in copied:
            this_color.append('cut' if self.fm.do_cut else 'copied')

        if drawn.is_link:
            this_color.append('link')
            this_color.append(drawn.exists and 'good' or 'bad')

        return this_color

    def _get_scroll_begin(self):
        """Determines scroll_begin (the position of the first displayed file)"""
        offset = self.settings.scroll_offset
        dirsize = len(self.target)
        winsize = self.hei
        halfwinsize = winsize // 2
        index = self.target.pointer or 0
        original = self.target.scroll_begin
        projected = index - original

        upper_limit = winsize - 1 - offset
        lower_limit = offset

        if original < 0:
            return 0

        if dirsize < winsize:
            return 0

        if halfwinsize < offset:
            return min( dirsize - winsize, max( 0, index - halfwinsize ))

        if original > dirsize - winsize:
            self.target.scroll_begin = dirsize - winsize
            return self._get_scroll_begin()

        if projected < upper_limit and projected > lower_limit:
            return original

        if projected > upper_limit:
            return min( dirsize - winsize,
                    original + (projected - upper_limit))

        if projected < upper_limit:
            return max( 0,
                    original - (lower_limit - projected))

        return original

    def _set_scroll_begin(self):
        """Updates the scroll_begin value"""
        self.scroll_begin = self._get_scroll_begin()
        self.target.scroll_begin = self.scroll_begin

    def scroll(self, n):
        """scroll down by n lines"""
        self.need_redraw = True
        self.target.move(down=n)
        self.target.scroll_begin += 3 * n

    def __str__(self):
        return self.__class__.__name__ + ' at level ' + str(self.level)
