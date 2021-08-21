# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""The Console widget implements a vim-like console"""

from __future__ import (absolute_import, division, print_function)

import curses
import os
import re
from collections import deque
from logging import getLogger

from ranger import PY3
from ranger.gui.widgets import Widget
from ranger.ext.direction import Direction
from ranger.ext.keybinding_parser import special_keys
from ranger.ext.widestring import uwid, WideString
from ranger.container.history import History, HistoryEmptyException
import ranger

LOG = getLogger(__name__)
CONSOLE_KEYMAPS = [ 'console', 'viconsole' ]


class Console(Widget):  # pylint: disable=too-many-instance-attributes,too-many-public-methods
    visible = False
    last_cursor_mode = None
    history_search_pattern = None
    prompt = ':'
    copy = ''
    tab_deque = None
    original_line = None
    history = None
    history_backup = None
    override = None
    allow_close = False
    historypath = None
    wait_for_command_input = False
    unicode_buffer = ""

    def __init__(self, win):
        Widget.__init__(self, win)
        self.pos = 0
        self.line = ''
        self.undo_pos = 0
        self.undo_line = ''
        self.vi_repeat = None
        self.insertmode = True
        self.history = History(self.settings.max_console_history_size)
        # load history from files
        if not ranger.args.clean:
            self.historypath = self.fm.datapath('history')
            if os.path.exists(self.historypath):
                try:
                    with open(self.historypath, "r") as fobj:
                        try:
                            for line in fobj:
                                self.history.add(line[:-1])
                        except UnicodeDecodeError as ex:
                            self.fm.notify(
                                "Failed to parse corrupt history file",
                                bad=True,
                                exception=ex,
                            )
                except (OSError, IOError) as ex:
                    self.fm.notify(
                        "Failed to read history file", bad=True, exception=ex
                    )
        self.history_backup = History(self.history)

        # NOTE: the console is considered in the "question mode" when the
        # question_queue is non-empty.  In that case, the console will draw the
        # question instead of the regular console, and the input you give is
        # used to answer the question instead of typing in commands.
        #
        # A question is a tuple of (question_string, callback_func,
        # tuple_of_choices).  callback_func is a function that is called when
        # the question is answered which gets the answer as an argument.
        # tuple_of_choices looks like ('y', 'n').  Only one-letter-answers are
        # currently supported.  Pressing enter uses the first choice whereas
        # pressing ESC uses the second choice.
        self.question_queue = []

    def destroy(self):
        # save history to files
        if ranger.args.clean or not self.settings.save_console_history:
            return
        if self.historypath:
            try:
                with open(self.historypath, 'w') as fobj:
                    for entry in self.history_backup:
                        try:
                            fobj.write(entry + '\n')
                        except UnicodeEncodeError:
                            pass
            except (OSError, IOError) as ex:
                self.fm.notify(
                    "Failed to write history file", bad=True, exception=ex
                )
        Widget.destroy(self)

    def _calculate_offset(self):
        wid = self.wid - 2
        whalf = wid // 2
        if self.pos < whalf or len(self.line) < wid:
            return 0
        if self.pos > len(self.line) - (wid - whalf):
            return len(self.line) - wid
        return self.pos - whalf

    def draw(self):
        self.win.erase()
        if self.question_queue:
            assert isinstance(self.question_queue[0], tuple)
            assert len(self.question_queue[0]) == 3
            self.addstr(0, 0, self.question_queue[0][0][self.pos:])
            return

        self.addstr(0, 0, self.prompt)
        line = WideString(self.line)
        if line:
            x = self._calculate_offset()
            self.addstr(0, len(self.prompt), str(line[x:]))

    def set_insertmode(self, enable):
        self.insertmode = enable
        self.fm.ui.keymaps.use_keymap(CONSOLE_KEYMAPS[0 if enable else 1])
        self.fm.ui.set_cursor_shape(self.settings.console_cursor if enable
            else self.settings.viconsole_cursor)

    def finalize(self):
        move = self.fm.ui.win.move
        if self.question_queue:
            try:
                move(self.y, len(self.question_queue[0][0]))
            except curses.error:
                pass
        else:
            try:
                x = self._calculate_offset()
                pos = uwid(self.line[x:self.pos]) + len(self.prompt)
                move(self.y, self.x + min(self.wid - 1, pos))
            except curses.error:
                pass

    def open(self, string='', prompt=None, position=None, viconsole=False):
        if prompt is not None:
            assert isinstance(prompt, str)
            self.prompt = prompt
        elif 'prompt' in self.__dict__:
            del self.prompt

        if self.last_cursor_mode is None:
            try:
                self.last_cursor_mode = curses.curs_set(1)
            except curses.error:
                pass
        self.allow_close = False
        self.tab_deque = None
        self.unicode_buffer = ""
        self.line = string
        self.history_search_pattern = self.line
        self.pos = len(string) - (1 if viconsole else 0)
        if position is not None:
            self.pos = min(self.pos, position)
        self.undo_pos = self.pos
        self.undo_line = self.line
        self.history_backup.fast_forward()
        self.history = History(self.history_backup)
        self.history.add('')
        self.wait_for_command_input = True

        self.set_insertmode(not viconsole)
        return True

    def close(self, trigger_cancel_function=True):
        if self.question_queue:
            question = self.question_queue[0]
            answers = question[2]
            if len(answers) >= 2:
                self._answer_question(answers[1])
        else:
            self._close_command_prompt(trigger_cancel_function)

    def _close_command_prompt(self, trigger_cancel_function=True):
        if trigger_cancel_function:
            cmd = self._get_cmd(quiet=True)
            if cmd:
                cmd.cancel()
        self.set_insertmode(True) # reset to default
        self.fm.ui.set_cursor_shape()
        if self.last_cursor_mode is not None:
            try:
                curses.curs_set(self.last_cursor_mode)
            except curses.error:
                pass
            self.last_cursor_mode = None
        self.fm.hide_console_info()
        self.add_to_history()
        self.tab_deque = None
        self.clear()
        self.__class__ = Console
        self.wait_for_command_input = False

    def clear(self):
        self.pos = 0
        self.line = ''

    def press(self, key):
        # if the console is in question mode don't process any keymaps
        if self.question_queue:
            if key == special_keys["enter"]:
                self.execute()
            elif key == special_keys["esc"]:
                self.close()
            else:
                self.type_key(key)
        else:
            # make sure we are in a valid console mode
            if self.fm.ui.keymaps.used_keymap not in CONSOLE_KEYMAPS:
                self.set_insertmode(True)
            if not self.fm.ui.press(key):
                # only insertmode allows typing
                if self.fm.ui.keymaps.used_keymap == CONSOLE_KEYMAPS[0]:
                    self.type_key(key)

    def _answer_question(self, answer):
        if not self.question_queue:
            return False
        question = self.question_queue[0]
        _, callback, answers = question
        if answer in answers:
            self.question_queue.pop(0)
            callback(answer)
            return True
        return False

    def type_key(self, key):
        self.tab_deque = None

        line = "" if self.question_queue else self.line
        result = self._add_character(key, self.unicode_buffer, line, self.pos)
        if result[1] == line:
            # line didn't change, so we don't need to do anything, just update
            # the unicode _buffer.
            self.unicode_buffer = result[0]
            return

        if self.question_queue:
            self.unicode_buffer, answer, _ = result
            self._answer_question(answer)
        else:
            self.unicode_buffer, self.line, self.pos = result
            self.on_line_change()

    @staticmethod
    def _add_character(key, unicode_buffer, line, pos):
        # Takes the pressed key, a string "unicode_buffer" containing a
        # potentially incomplete unicode character, the current line and the
        # position of the cursor inside the line.
        # This function returns the new unicode buffer, the modified line and
        # position.
        if isinstance(key, int):
            try:
                key = chr(key)
            except ValueError:
                return unicode_buffer, line, pos

        if PY3:
            if len(unicode_buffer) >= 4:
                unicode_buffer = ""
            if ord(key) in range(0, 256):
                unicode_buffer += key
                try:
                    decoded = unicode_buffer.encode("latin-1").decode("utf-8")
                except UnicodeDecodeError:
                    return unicode_buffer, line, pos
                except UnicodeEncodeError:
                    return unicode_buffer, line, pos
                else:
                    unicode_buffer = ""
                    if pos == len(line):
                        line += decoded
                    else:
                        line = line[:pos] + decoded + line[pos:]
                    pos += len(decoded)
        else:
            if pos == len(line):
                line += key
            else:
                line = line[:pos] + key + line[pos:]
            pos += len(key)
        return unicode_buffer, line, pos

    def history_move(self, n):
        try:
            current = self.history.current()
        except HistoryEmptyException:
            pass
        else:
            if self.line != current and self.line != self.history.top():
                self.history.modify(self.line)
            if self.history_search_pattern:
                self.history.search(self.history_search_pattern, n)
            else:
                self.history.move(n)
            current = self.history.current()
            if self.line != current:
                self.line = self.history.current()
                self.pos = len(self.line)

    def add_to_history(self):
        self.history_backup.fast_forward()
        self.history_backup.add(self.line)
        self.history = History(self.history_backup)

    def move(self, **keywords):
        direction = Direction(keywords)
        if direction.horizontal():
            # Ensure that the pointer is moved utf-char-wise
            if PY3:
                if self.question_queue:
                    umax = len(self.question_queue[0][0]) + 1 - self.wid
                else:
                    umax = len(self.line) + 1
                self.pos = direction.move(
                    direction=direction.right(),
                    minimum=0,
                    maximum=umax,
                    current=self.pos)
            else:
                if self.question_queue:
                    uchar = list(self.question_queue[0][0].decode('utf-8', 'ignore'))
                    upos = len(self.question_queue[0][0][:self.pos].decode('utf-8', 'ignore'))
                    umax = len(uchar) + 1 - self.wid
                else:
                    uchar = list(self.line.decode('utf-8', 'ignore'))
                    upos = len(self.line[:self.pos].decode('utf-8', 'ignore'))
                    umax = len(uchar) + 1
                newupos = direction.move(
                    direction=direction.right(),
                    minimum=0,
                    maximum=umax,
                    current=upos)
                self.pos = len(''.join(uchar[:newupos]).encode('utf-8', 'ignore'))

    def move_word(self, **keywords):
        direction = Direction(keywords)
        if direction.horizontal():
            self.pos = self.move_by_word(self.line, self.pos, direction.right())
            self.on_line_change()

    class ViMotion(object):
        # this class allows us to handle the following motions:
        # eE start next, skip ws, skip c,  stay on last
        # bB start prev, skip ws, skip c,  stay on last
        # wW start curr, skip c,  skip ws, stay on next

        def __init__(self, pos, line, direction):
            self.pos = pos
            self.line = line
            self.direction = direction

        def at_end(self, direction=None, edge=False):
            # we do not allow the cursor to move past the end unless edge is set
            if (direction or self.direction) > 0:
                return self.pos >= len(self.line) - (0 if edge else 1)
            else:
                return self.pos <= 0

        def move(self, transform=1, edge=False):
            if not self.at_end(self.direction * transform, edge):
                self.pos += self.direction * transform
                return self.pos
            else:
                return -1

        def skip_ws(self):
            while not self.at_end():
                if not self.line[self.pos].isspace():
                    break
                self.move()

        def skip_c(self, anychar, stay_on_last):
            start = self.pos
            while not self.at_end():
                ccc = self.line[self.pos]
                if anychar:
                    if ccc.isspace():
                        break
                else:
                    if not (ccc.isalnum() or ccc == '_'):
                        break
                self.move()
            if stay_on_last and self.pos != start and not self.at_end():
                self.move(-1)

            if start == self.pos and not anychar:
                # did not move - check alternate
                while not self.at_end():
                    ccc = self.line[self.pos]
                    if ccc.isalnum() or ccc.isspace():
                        break
                    self.move()
                return False
            return True

        def m_eb(self, anychar):
            self.move()
            self.skip_ws()
            if not self.skip_c(anychar, stay_on_last=True):
                self.skip_c(anychar, stay_on_last=True)
            return self.pos

        def m_w(self, anychar):
            self.skip_c(anychar, stay_on_last=False)
            self.skip_ws()
            return self.pos

        def m_ft(self, arg, till_before, repeat):
            start = self.pos
            self.move()
            if repeat:
                # this allows us to correctly process
                # 2tK vs tK+tK
                start = self.pos
            while not self.at_end():
                if self.line[self.pos] == arg and not \
                   (repeat and till_before and start == self.pos):
                    if till_before and self.pos != start:
                        self.move(-1)
                    return self.pos
                self.move()
            return -1

        def m_end(self):
            self.pos = max(0, len(self.line) - 1)
            return self.pos

    def vi_motion(self, quantifier, motion, arg=None):
        # handle repeat motion
        if motion == ";":
            motion, arg = self.vi_repeat
            is_repeat = True
        elif motion == ",":
            motion, arg = self.vi_repeat[0].swapcase(), self.vi_repeat[1]
            is_repeat = True
        else:
            is_repeat = False

        direction = -1 if motion in ["h", "b", "B", "F", "T"] else 1
        vim = Console.ViMotion(self.pos, self.line, direction)
        if motion == "0":
            pos = 0
        elif motion == "$":
            pos = vim.m_end()
        elif motion in ["h", "l"]:
            for i in range(quantifier):
                vim.move()
            pos = vim.pos
        elif motion in ["f", "F", "t", "T"]:
            for i in range(quantifier):
                pos = vim.m_ft(arg, motion in ["t", "T"], is_repeat or i > 0)
            if not is_repeat:
                self.vi_repeat = (motion, arg)
        elif motion in ["e", "b"]:
            for i in range(quantifier):
                pos = vim.m_eb(False)
        elif motion in ["E", "B"]:
            for i in range(quantifier):
                pos = vim.m_eb(True)
        elif motion in ["w", "W"]:
            for i in range(quantifier):
                pos = vim.m_w(motion == "W")
        else:
            LOG.error("unknown motion go %s", motion)
            return
        if pos >= 0:
            self.pos = pos
        self.on_line_change()

    def vi_mod(self, mode, quantifier, motion, arg=None):
        def cut(start, end):
            if start <= end:
                self.copy = self.line[start:end + 1]
                if mode != "y":
                    self.line = self.line[:start] + self.line[end + 1:]

        direction = -1 if motion in ["h", "b", "B", "F", "T"] else 1
        vim = Console.ViMotion(self.pos, self.line, direction)

        pos = -1
        if motion == "0":
            if self.pos > 0:
                cut(0, self.pos - 1)
            pos = 0
        elif motion == "$":
            to_pos = vim.m_end()
            cut(self.pos, to_pos)
            if self.pos > 0:
                pos = self.pos - 1
        elif motion == "h":
            for i in range(quantifier):
                vim.move()
            to_pos = vim.pos
            cut(to_pos, self.pos - 1)
            pos = to_pos
        elif motion == "l":
            for i in range(quantifier):
                vim.move(edge=True)
            to_pos = vim.pos
            cut(self.pos, to_pos - 1)
            if self.pos >= len(self.line):
                pos = len(self.line) - 1
        elif motion in ["f", "t"]:
            for i in range(quantifier):
                to_pos = vim.m_ft(arg, motion == "t", i > 0)
            if to_pos >= 0:
                cut(self.pos, to_pos)
        elif motion in ["F", "T"]:
            for i in range(quantifier):
                to_pos = vim.m_ft(arg, motion == "T", i > 0)
            if to_pos >= 0:
                cut(to_pos, self.pos)
                pos = to_pos
        elif motion in ["e", "E"]:
            for i in range(quantifier):
                to_pos = vim.m_eb(motion == "E")
            cut(self.pos, to_pos)
        elif motion in ["b", "B"]:
            for i in range(quantifier):
                to_pos = vim.m_eb(motion == "B")
            if to_pos < self.pos:
                cut(to_pos, self.pos - 1)
                pos = to_pos
        elif motion in ["w", "W"]:
            for i in range(quantifier):
                to_pos = vim.m_w(motion == "W")
            if to_pos > self.pos:
                if to_pos < len(self.line) - 1:
                    to_pos -= 1
                cut(self.pos, to_pos)
        elif motion == mode: # dd, cc, yy
            self.copy = self.line
            if mode != "y":
                self.line = ""
                pos = 0
        else:
            LOG.error("unknown motion delete %s", motion)
            return
        if mode != "y" and pos >= 0:
            self.pos = pos
            self.on_line_change()

    def vi_mod_r(self, quantifier, key):
        count = quantifier or 1
        start = self.pos
        end = start + count
        if end <= len(self.line):
            self.line = self.line[:start] + (key * count) + self.line[end:]
            self.on_line_change()

    def set_undo(self, line=None):
        self.undo_line = line if line else self.line
        self.undo_pos = 0 if line else self.pos

    def vi_undo(self):
        self.undo_line, self.line = self.line, self.undo_line
        self.undo_pos, self.pos = self.pos, self.undo_pos
        self.on_line_change()

    @staticmethod
    def move_by_word(line, position, direction):
        """
        Returns a new position by moving word-wise in the line

        >>> from ranger import PY3
        >>> if PY3:
        ...     line = "\\u30AA\\u30CF\\u30E8\\u30A6 world,  this is dog"
        ... else:
        ...     # Didn't get the unicode test to work on python2, even though
        ...     # it works fine in ranger, even with unicode input...
        ...     line = "ohai world,  this is dog"
        >>> Console.move_by_word(line, 0, -1)
        0
        >>> Console.move_by_word(line, 0, 1)
        5
        >>> Console.move_by_word(line, 2, -1)
        0
        >>> Console.move_by_word(line, 2, 1)
        5
        >>> Console.move_by_word(line, 15, -2)
        5
        >>> Console.move_by_word(line, 15, 2)
        21
        >>> Console.move_by_word(line, 24, -1)
        21
        >>> Console.move_by_word(line, 24, 1)
        24
        """
        word_beginnings = []
        seen_whitespace = True
        current_word = None
        cursor_inside_word = False

        # Scan the line for word boundaries and determine position of cursor
        for i, char in enumerate(line):
            if i == position:
                current_word = len(word_beginnings)
                if not seen_whitespace:
                    cursor_inside_word = True
            if char == " ":
                seen_whitespace = True
            elif seen_whitespace:
                seen_whitespace = False
                word_beginnings.append(i)
        word_beginnings.append(len(line))

        # Handle corner cases:
        if current_word is None:
            current_word = len(word_beginnings)
        if direction > 0 and cursor_inside_word:
            current_word -= 1
        if direction < 0 and position == len(line):
            current_word -= 1

        new_word = current_word + direction
        new_word = max(0, min(len(word_beginnings) - 1, new_word))

        return word_beginnings[new_word]

    def delete_rest(self, direction):
        self.tab_deque = None
        if direction > 0:
            self.copy = self.line[self.pos:]
            self.line = self.line[:self.pos]
        else:
            self.copy = self.line[:self.pos]
            self.line = self.line[self.pos:]
            self.pos = 0
        self.on_line_change()

    def paste(self):
        if self.pos == len(self.line):
            self.line += self.copy
        else:
            self.line = self.line[:self.pos] + self.copy + self.line[self.pos:]
        self.pos += len(self.copy)
        self.on_line_change()

    def delete_word(self, backward=True):
        if self.line:
            self.tab_deque = None
            if backward:
                right_part = self.line[self.pos:]
                i = self.pos - 2
                while i >= 0 and re.match(
                        r'[\w\d]', self.line[i], re.UNICODE):  # pylint: disable=no-member
                    i -= 1
                self.copy = self.line[i + 1:self.pos]
                self.line = self.line[:i + 1] + right_part
                self.pos = i + 1
            else:
                left_part = self.line[:self.pos]
                i = self.pos + 1
                while i < len(self.line) and re.match(
                        r'[\w\d]', self.line[i], re.UNICODE):  # pylint: disable=no-member
                    i += 1
                self.copy = self.line[self.pos:i]
                if i >= len(self.line):
                    self.line = left_part
                    self.pos = len(self.line)
                else:
                    self.line = left_part + self.line[i:]
                    self.pos = len(left_part)
            self.on_line_change()

    def delete(self, mod):
        self.tab_deque = None
        if mod == -1 and self.pos == 0:
            if not self.line:
                self.close(trigger_cancel_function=False)
            return
        # Delete utf-char-wise
        if PY3:
            left_part = self.line[:self.pos + mod]
            self.pos = len(left_part)
            self.line = left_part + self.line[self.pos + 1:]
        else:
            uchar = list(self.line.decode('utf-8', 'ignore'))
            upos = len(self.line[:self.pos].decode('utf-8', 'ignore')) + mod
            left_part = ''.join(uchar[:upos]).encode('utf-8', 'ignore')
            self.pos = len(left_part)
            self.line = left_part + ''.join(uchar[upos + 1:]).encode('utf-8', 'ignore')
        self.on_line_change()

    def transpose_subr(self, line, x, y):
        # Transpose substrings x & y of line
        # x & y are tuples of length two containing positions of endpoints
        if not 0 <= x[0] < x[1] <= y[0] < y[1] <= len(line):
            self.fm.notify("Tried to transpose invalid regions.", bad=True)
            return line

        line_begin = line[:x[0]]
        word_x = line[x[0]:x[1]]
        line_middle = line[x[1]:y[0]]
        word_y = line[y[0]:y[1]]
        line_end = line[y[1]:]

        line = line_begin + word_y + line_middle + word_x + line_end
        return line

    def transpose_chars(self):
        if self.pos == 0:
            return
        elif self.pos == len(self.line):
            x = max(0, self.pos - 2), max(0, self.pos - 1)
            y = max(0, self.pos - 1), self.pos
        else:
            x = max(0, self.pos - 1), self.pos
            y = self.pos, min(len(self.line), self.pos + 1)
        self.line = self.transpose_subr(self.line, x, y)
        self.pos = y[1]
        self.on_line_change()

    def transpose_words(self):
        # Interchange adjacent words at the console with Alt-t
        # like in Emacs and many terminal emulators
        if self.line:
            # If before the first word, interchange next two words
            if not re.search(r'[\w\d]', self.line[:self.pos], re.UNICODE):
                self.pos = self.move_by_word(self.line, self.pos, 1)

            # If in/after last word, interchange last two words
            if (re.match(r'[\w\d]*\s*$', self.line[self.pos:], re.UNICODE)
                and (re.match(r'[\w\d]', self.line[self.pos - 1], re.UNICODE)
                     if self.pos - 1 >= 0 else True)):
                self.pos = self.move_by_word(self.line, self.pos, -1)

            # Util function to increment position until out of word/whitespace
            def _traverse(line, pos, regex):
                while pos < len(line) and re.match(
                        regex, line[pos], re.UNICODE):
                    pos += 1
                return pos

            # Calculate endpoints of target words and pass them to
            # 'self.transpose_subr'
            x_begin = self.move_by_word(self.line, self.pos, -1)
            x_end = _traverse(self.line, x_begin, r'[\w\d]')
            x = x_begin, x_end

            y_begin = self.pos

            # If in middle of word, move to end
            if re.match(r'[\w\d]', self.line[self.pos - 1], re.UNICODE):
                y_begin = _traverse(self.line, y_begin, r'[\w\d]')

            # Traverse whitespace to beginning of next word
            y_begin = _traverse(self.line, y_begin, r'\s')

            y_end = _traverse(self.line, y_begin, r'[\w\d]')
            y = y_begin, y_end

            self.line = self.transpose_subr(self.line, x, y)
            self.pos = y[1]
            self.on_line_change()

    def execute(self, cmd=None):
        if self.question_queue and cmd is None:
            question = self.question_queue[0]
            answers = question[2]
            if len(answers) >= 1:
                self._answer_question(answers[0])
            else:
                self.question_queue.pop(0)
            return

        self.allow_close = True
        if cmd:
            cmd.execute()
        else:
            self.fm.execute_console(self.line)

        if self.allow_close:
            self._close_command_prompt(trigger_cancel_function=False)

    def _get_cmd(self, quiet=False):
        try:
            command_class = self.get_cmd_class()
        except IndexError:
            return None
        except KeyError:
            if not quiet:
                self.fm.notify("Command not found: `%s'" % self.line.split()[0], bad=True)
            return None
        return command_class(self.line)

    def get_cmd_class(self):
        return self.fm.commands.get_command(self.line.split()[0], abbrev=True)

    def _get_tab(self, tabnum):
        if ' ' in self.line:
            cmd = self._get_cmd()
            if cmd:
                return cmd.tab(tabnum)
            return None

        return self.fm.commands.command_generator(self.line)

    def tab(self, tabnum=1):
        if self.tab_deque is None:
            tab_result = self._get_tab(tabnum)

            if tab_result is None:
                pass
            elif isinstance(tab_result, str):
                self.line = tab_result
                self.pos = len(tab_result)
                self.on_line_change()
            elif hasattr(tab_result, '__iter__'):
                self.tab_deque = deque(tab_result)
                self.tab_deque.appendleft(self.line)

        if self.tab_deque is not None:
            self.tab_deque.rotate(-tabnum)
            self.line = self.tab_deque[0]
            self.pos = len(self.line)
            self.on_line_change()

    def on_line_change(self):
        self.history_search_pattern = self.line
        try:
            cls = self.get_cmd_class()
        except (KeyError, ValueError, IndexError):
            pass
        else:
            cmd = cls(self.line)
            if cmd and cmd.quick():
                cmd.quickly_executed = True
                self.execute(cmd)

    def ask(self, text, callback, choices=None):
        """Open a question prompt with predefined choices

        The "text" is displayed as the question text and should include a list
        of possible keys that the user can type.  The "callback" is a function
        that is called when the question is answered.  It only gets the answer
        as an argument.  "choices" is a tuple of one-letter strings that can be
        typed in by the user.  Every other input gets ignored, except <Enter>
        and <ESC>.

        The first choice is used when the user presses <Enter>, the second
        choice is used when the user presses <ESC>.
        """
        self.question_queue.append(
            (text, callback, choices if choices is not None else ['y', 'n']))


if __name__ == '__main__':
    import doctest
    import sys
    sys.exit(doctest.testmod()[0])
