# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""Interrupt Signal handler for curses

This module can catch interrupt signals which would otherwise
rise a KeyboardInterrupt exception and handle it by pushing
a Ctrl+C (ASCII value 3) to the curses getch stack.
"""

from __future__ import (absolute_import, print_function)

import curses
import signal

_do_catch_interrupt = True  # pylint: disable=invalid-name


def catch_interrupt(boolean=True):
    """Should interrupts be caught and simulate a ^C press in curses?"""
    global _do_catch_interrupt  # pylint: disable=global-statement,invalid-name
    old_value = _do_catch_interrupt
    _do_catch_interrupt = bool(boolean)
    return old_value

# The handler which will be used in signal.signal()


def _interrupt_handler(signum, frame):
    # if a keyboard-interrupt occurs...
    if _do_catch_interrupt:
        # push a Ctrl+C (ascii value 3) to the curses getch stack
        curses.ungetch(3)
    else:
        # use the default handler
        signal.default_int_handler(signum, frame)


def install_interrupt_handler():
    """Install the custom interrupt_handler"""
    signal.signal(signal.SIGINT, _interrupt_handler)


def restore_interrupt_handler():
    """Restore the default_int_handler"""
    signal.signal(signal.SIGINT, signal.default_int_handler)
