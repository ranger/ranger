# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""The Console widget implements a vim-like console"""

from __future__ import (absolute_import, division, print_function)

import curses
import os
import re
from collections import deque

from ranger.gui.widgets import Widget
from ranger.ext.direction import Direction
from ranger.ext.widestring import uwid, WideString
from ranger.container.history import History, HistoryEmptyException
import ranger


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
        self.history = History(self.settings.max_console_history_size)
        # load history from files
        if not ranger.args.clean:
            self.historypath = self.fm.datapath('history')
            if os.path.exists(self.historypath):
                try:
                    fobj = open(self.historypath, 'r')
                except OSError as ex:
                    self.fm.notify('Failed to read history file', bad=True, exception=ex)
                else:
                    try:
                        for line in fobj:
                            self.history.add(line[:-1])
                    except UnicodeDecodeError as ex:
                        self.fm.notify('Failed to parse corrupt history file',
                                       bad=True, exception=ex)
                    fobj.close()
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
                fobj = open(self.historypath, 'w')
            except OSError as ex:
                self.fm.notify('Failed to write history file', bad=True, exception=ex)
            else:
                for entry in self.history_backup:
                    try:
                        fobj.write(entry + '\n')
                    except UnicodeEncodeError:
                        pass
                fobj.close()
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

    def open(self, string='', prompt=None, position=None):
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
        self.pos = len(string)
        if position is not None:
            self.pos = min(self.pos, position)
        self.history_backup.fast_forward()
        self.history = History(self.history_backup)
        self.history.add('')
        self.wait_for_command_input = True
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
        self.fm.ui.keymaps.use_keymap('console')
        if not self.fm.ui.press(key):
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

    def _add_character(self, key, unicode_buffer, line, pos):
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

        if self.fm.py3:
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
            if self.fm.py3:
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

    @staticmethod
    def move_by_word(line, position, direction):
        """
        Returns a new position by moving word-wise in the line

        >>> import sys
        >>> if sys.version_info < (3, ):
        ...     # Didn't get the unicode test to work on python2, even though
        ...     # it works fine in ranger, even with unicode input...
        ...     line = "ohai world,  this is dog"
        ... else:
        ...     line = "\\u30AA\\u30CF\\u30E8\\u30A6 world,  this is dog"
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
        if self.fm.py3:
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
    doctest.testmod()
