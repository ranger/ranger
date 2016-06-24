# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# Author: David Barnett <davidbarnett2@gmail.com>, 2010

"""A library to help to convert ANSI codes to curses instructions."""

from ranger.gui import color
import re

ansi_re = re.compile('(\x1b' + r'\[\d*(?:;\d+)*?[a-zA-Z])')
codesplit_re = re.compile('38;5;(\d+);|48;5;(\d+);|(\d*);')
reset = '\x1b[0m'


def split_ansi_from_text(ansi_text):
    return ansi_re.split(ansi_text)

# For information on the ANSI codes see
# githttp://en.wikipedia.org/wiki/ANSI_escape_code


def text_with_fg_bg_attr(ansi_text):
    fg, bg, attr = -1, -1, 0
    for chunk in split_ansi_from_text(ansi_text):
        if chunk and chunk[0] == '\x1b':
            if chunk[-1] != 'm':
                continue
            match = re.match(r'^.\[(.*).$', chunk)
            if not match:
                # XXX I have no test case to determine what should happen here
                continue
            attr_args = match.group(1)

            # Convert arguments to attributes/colors
            for x256fg, x256bg, arg in codesplit_re.findall(attr_args + ';'):
                # first handle xterm256 codes
                try:
                    if len(x256fg) > 0:           # xterm256 foreground
                        fg = int(x256fg)
                        continue
                    elif len(x256bg) > 0:         # xterm256 background
                        bg = int(x256bg)
                        continue
                    elif len(arg) > 0:            # usual ansi code
                        n = int(arg)
                    else:                         # empty code means reset
                        n = 0
                except Exception:
                    continue

                if n == 0:                        # reset colors and attributes
                    fg, bg, attr = -1, -1, 0

                elif n == 1:                      # enable attribute
                    attr |= color.bold
                elif n == 4:
                    attr |= color.underline
                elif n == 5:
                    attr |= color.blink
                elif n == 7:
                    attr |= color.reverse
                elif n == 8:
                    attr |= color.invisible

                elif n == 22:                     # disable attribute
                    attr &= not color.bold
                elif n == 24:
                    attr &= not color.underline
                elif n == 25:
                    attr &= not color.blink
                elif n == 27:
                    attr &= not color.reverse
                elif n == 28:
                    attr &= not color.invisible

                elif n >= 30 and n <= 37:         # 8 ansi foreground and background colors
                    fg = n - 30
                elif n == 39:
                    fg = -1
                elif n >= 40 and n <= 47:
                    bg = n - 40
                elif n == 49:
                    bg = -1

                elif n >= 90 and n <= 97:         # 8 aixterm high intensity colors (light but not bold)
                    fg = n - 90 + 8
                elif n == 99:
                    fg = -1
                elif n >= 100 and n <= 107:
                    bg = n - 100 + 8
                elif n == 109:
                    bg = -1

            yield (fg, bg, attr)

        else:
            yield chunk


def char_len(ansi_text):
    """Count the number of visible characters.

    >>> char_len("\x1b[0;30;40mX\x1b[0m")
    1
    >>> char_len("\x1b[0;30;40mXY\x1b[0m")
    2
    >>> char_len("\x1b[0;30;40mX\x1b[0mY")
    2
    >>> char_len("hello")
    5
    >>> char_len("")
    0
    """
    return len(ansi_re.sub('', ansi_text))


def char_slice(ansi_text, start, length):
    """Slices a string with respect to ansi code sequences

    Acts as if the ansi codes aren't there, slices the text from the
    given start point to the given length and adds the codes back in.

    >>> test_string = "abcde\x1b[30mfoo\x1b[31mbar\x1b[0mnormal"
    >>> split_ansi_from_text(test_string)
    ['abcde', '\\x1b[30m', 'foo', '\\x1b[31m', 'bar', '\\x1b[0m', 'normal']
    >>> char_slice(test_string, 1, 3)
    'bcd'
    >>> char_slice(test_string, 5, 6)
    '\\x1b[30mfoo\\x1b[31mbar'
    >>> char_slice(test_string, 0, 8)
    'abcde\\x1b[30mfoo'
    >>> char_slice(test_string, 4, 4)
    'e\\x1b[30mfoo'
    >>> char_slice(test_string, 11, 100)
    '\\x1b[0mnormal'
    >>> char_slice(test_string, 9, 100)
    '\\x1b[31mar\\x1b[0mnormal'
    >>> char_slice(test_string, 9, 4)
    '\\x1b[31mar\\x1b[0mno'
    """
    chunks = []
    last_color = ""
    pos = old_pos = 0
    for i, chunk in enumerate(split_ansi_from_text(ansi_text)):
        if i % 2 == 1:
            last_color = chunk
            continue

        old_pos = pos
        pos += len(chunk)
        if pos <= start:
            pass  # seek
        elif old_pos < start and pos >= start:
            chunks.append(last_color)
            chunks.append(chunk[start - old_pos:start - old_pos + length])
        elif pos > length + start:
            chunks.append(last_color)
            chunks.append(chunk[:start - old_pos + length])
        else:
            chunks.append(last_color)
            chunks.append(chunk)
        if pos - start >= length:
            break
    return ''.join(chunks)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
