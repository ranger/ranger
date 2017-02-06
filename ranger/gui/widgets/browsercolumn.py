# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""The BrowserColumn widget displays the contents of a directory or file."""

from __future__ import (absolute_import, division, print_function)

import curses
import stat
from time import time
from os.path import splitext

from ranger.ext.widestring import WideString
from ranger.core import linemode

from . import Widget
from .pager import Pager


class BrowserColumn(Pager):  # pylint: disable=too-many-instance-attributes
    main_column = False
    display_infostring = False
    display_vcsstate = True
    scroll_begin = 0
    target = None
    last_redraw_time = -1

    old_dir = None
    old_thisfile = None

    def __init__(self, win, level, tab=None):
        """Initializes a Browser Column Widget

        win = the curses window object of the BrowserView
        level = what to display?

        level >0 => previews
        level 0 => current file/directory
        level <0 => parent directories
        """
        Pager.__init__(self, win)
        Widget.__init__(self, win)  # pylint: disable=non-parent-init-called
        self.level = level
        self.tab = tab
        self.original_level = level

        self.settings.signal_bind('setopt.display_size_in_main_column',
                                  self.request_redraw, weak=True)

    def request_redraw(self):
        self.need_redraw = True

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
                    except IndexError:
                        pass
                    else:
                        if clicked_file.is_directory:
                            self.fm.enter_dir(clicked_file.path, remember=True)
                        elif self.level == 0:
                            self.fm.thisdir.move_to_obj(clicked_file)
                            self.fm.execute_file(clicked_file)

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
        except curses.error:
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
        if self.tab is None:
            tab = self.fm.thistab
        else:
            tab = self.tab
        self.target = tab.at_level(self.level)

    def draw(self):
        """Call either _draw_file() or _draw_directory()"""
        target = self.target

        if target != self.old_dir:
            self.need_redraw = True
            self.old_dir = target

        if target:
            target.use()

            if target.is_directory and (self.level <= 0 or self.settings.preview_directories):
                if self.old_thisfile != target.pointed_obj:
                    self.old_thisfile = target.pointed_obj
                    self.need_redraw = True
                self.need_redraw |= target.load_content_if_outdated()
                self.need_redraw |= target.sort_if_outdated()
                self.need_redraw |= self.last_redraw_time < target.last_update_time
                if target.pointed_obj:
                    self.need_redraw |= target.pointed_obj.load_if_outdated()
                    self.need_redraw |= self.last_redraw_time < target.pointed_obj.last_load_time
            else:
                self.need_redraw |= target.load_if_outdated()
                self.need_redraw |= self.last_redraw_time < target.last_load_time

        if self.need_redraw:
            self.win.erase()
            if target is None:
                pass
            elif target.is_file:
                Pager.open(self)
                self._draw_file()
            elif target.is_directory:
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

        path = self.target.get_preview_source(self.wid, self.hei)
        if path is None:
            Pager.close(self)
        else:
            if self.target.is_image_preview():
                self.set_image(path)
            else:
                self.set_source(path)
            Pager.draw(self)

    def _format_line_number(self, linum_format, i, selected_i):
        line_number = i
        if self.settings.line_numbers == 'relative':
            line_number = abs(selected_i - i)
            if line_number == 0:
                line_number = selected_i

        return linum_format.format(line_number)

    def _draw_directory(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
            self):
        """Draw the contents of a directory"""
        if self.image:
            self.image = None
            self.need_clear_image = True
            Pager.clear_image(self)

        if self.level > 0 and not self.settings.preview_directories:
            return

        base_color = ['in_browser']

        if self.fm.ui.viewmode == 'multipane' and self.tab is not None:
            active_pane = self.tab == self.fm.thistab
            if active_pane:
                base_color.append('active_pane')
            else:
                base_color.append('inactive_pane')
        else:
            active_pane = False

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

        # Set the size of the linum text field to the number of digits in the
        # visible files in directory.
        linum_text_len = len(str(self.scroll_begin + self.hei))
        linum_format = "{0:>" + str(linum_text_len) + "}"
        # add separator between line number and tag
        linum_format += " "

        selected_i = self._get_index_of_selected_file()
        for line in range(self.hei):
            i = line + self.scroll_begin

            try:
                drawn = self.target.files[i]
            except IndexError:
                break

            tagged = self.fm.tags and drawn.realpath in self.fm.tags
            if tagged:
                tagged_marker = self.fm.tags.marker(drawn.realpath)
            else:
                tagged_marker = " "

            # Extract linemode-related information from the drawn object
            metadata = None
            current_linemode = drawn.linemode_dict[drawn.linemode]
            if current_linemode.uses_metadata:
                metadata = self.fm.metadata.get_metadata(drawn.path)
                if not all(getattr(metadata, tag)
                           for tag in current_linemode.required_metadata):
                    current_linemode = drawn.linemode_dict[linemode.DEFAULT_LINEMODE]

            metakey = hash(repr(sorted(metadata.items()))) if metadata else 0
            key = (self.wid, selected_i == i, drawn.marked, self.main_column,
                   drawn.path in copied, tagged_marker, drawn.infostring,
                   drawn.vcsstatus, drawn.vcsremotestatus, self.target.has_vcschild,
                   self.fm.do_cut, current_linemode.name, metakey, active_pane,
                   self.settings.line_numbers)

            # Check if current line has not already computed and cached
            if key in drawn.display_data:
                # Recompute line numbers because they can't be reliably cached.
                if self.main_column and self.settings.line_numbers != 'false':
                    line_number_text = self._format_line_number(linum_format,
                                                                i,
                                                                selected_i)
                    drawn.display_data[key][0][0] = line_number_text

                self.execute_curses_batch(line, drawn.display_data[key])
                self.color_reset()
                continue

            text = current_linemode.filetitle(drawn, metadata)

            if drawn.marked and (self.main_column or
                                 self.settings.display_tags_in_all_columns):
                text = " " + text

            # Computing predisplay data. predisplay contains a list of lists
            # [string, colorlst] where string is a piece of string to display,
            # and colorlst a list of contexts that we later pass to the
            # colorscheme, to compute the curses attribute.
            predisplay_left = []
            predisplay_right = []
            space = self.wid

            # line number field
            if self.settings.line_numbers != 'false':
                if self.main_column and space - linum_text_len > 2:
                    line_number_text = self._format_line_number(linum_format,
                                                                i,
                                                                selected_i)
                    predisplay_left.append([line_number_text, []])
                    space -= linum_text_len

                    # Delete one additional character for space separator
                    # between the line number and the tag
                    space -= 1

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
            infostring = []
            infostringlen = 0
            try:
                infostringdata = current_linemode.infostring(drawn, metadata)
                if infostringdata:
                    infostring.append([" " + infostringdata + " ",
                                       ["infostring"]])
            except NotImplementedError:
                infostring = self._draw_infostring_display(drawn, space)
            if infostring:
                infostringlen = self._total_len(infostring)
                if space - infostringlen > 2:
                    predisplay_right = infostring + predisplay_right
                    space -= infostringlen

            textstring = self._draw_text_display(text, space)
            textstringlen = self._total_len(textstring)
            predisplay_left += textstring
            space -= textstringlen

            assert space >= 0, "Error: there is not enough space to write the text. " \
                "I have computed spaces wrong."
            if space > 0:
                predisplay_left.append([' ' * space, []])

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

    def _get_index_of_selected_file(self):
        if self.fm.ui.viewmode == 'multipane' and self.tab:
            return self.tab.pointer
        return self.target.pointer

    @staticmethod
    def _total_len(predisplay):
        return sum([len(WideString(s)) for s, _ in predisplay])

    def _draw_text_display(self, text, space):
        wtext = WideString(text)
        wext = WideString(splitext(text)[1])
        wellip = WideString(self.ellipsis[self.settings.unicode_ellipsis])
        if len(wtext) > space:
            wtext = wtext[:max(1, space - len(wext) - len(wellip))] + wellip + wext
        # Truncate again if still too long.
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
        if (self.target.vcs and self.target.vcs.track) \
                or (drawn.is_directory and drawn.vcs and drawn.vcs.track):
            if drawn.vcsremotestatus:
                vcsstr, vcscol = self.vcsremotestatus_symb[drawn.vcsremotestatus]
                vcsstring_display.append([vcsstr, ['vcsremote'] + vcscol])
            elif self.target.has_vcschild:
                vcsstring_display.append([' ', []])
            if drawn.vcsstatus:
                vcsstr, vcscol = self.vcsstatus_symb[drawn.vcsstatus]
                vcsstring_display.append([vcsstr, ['vcsfile'] + vcscol])
            elif self.target.has_vcschild:
                vcsstring_display.append([' ', []])
        elif self.target.has_vcschild:
            vcsstring_display.append(['  ', []])

        return vcsstring_display

    def _draw_directory_color(self, i, drawn, copied):
        this_color = []
        if i == self._get_index_of_selected_file():
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

    def _get_scroll_begin(self):  # pylint: disable=too-many-return-statements
        """Determines scroll_begin (the position of the first displayed file)"""
        offset = self.settings.scroll_offset
        dirsize = len(self.target)
        winsize = self.hei
        halfwinsize = winsize // 2
        index = self._get_index_of_selected_file() or 0
        original = self.target.scroll_begin
        projected = index - original

        upper_limit = winsize - 1 - offset
        lower_limit = offset

        if original < 0:
            return 0

        if dirsize < winsize:
            return 0

        if halfwinsize < offset:
            return min(dirsize - winsize, max(0, index - halfwinsize))

        if original > dirsize - winsize:
            self.target.scroll_begin = dirsize - winsize
            return self._get_scroll_begin()

        if projected < upper_limit and projected > lower_limit:
            return original

        if projected > upper_limit:
            return min(dirsize - winsize, original + (projected - upper_limit))

        if projected < upper_limit:
            return max(0, original - (lower_limit - projected))

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
