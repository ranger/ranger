# -*- encoding: utf-8 -*-
# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import absolute_import

import os
import signal
from contextlib import contextmanager


@contextmanager
def handle_signal(signum, handler):
    """Register a signal handler `handler` for signal `signum`,
    which will be active for the duration of the block"""
    if handler is None:
        # None handlers refer to C functions and can't be installed from Python
        raise ValueError("Can't install None signal handler")
    prev_handler = signal.getsignal(signum)
    if prev_handler is None:
        # Same issue as with `handler`
        raise ValueError(
            "Currently installed handler is None, which is unsupported"
        )
    try:
        signal.signal(signum, handler)
        yield
    finally:
        signal.signal(signum, prev_handler)


def raise_signal(signum):
    """Raise signal number `signum`. Compatible with Python 2"""
    # COMPAT: signal.raise_signal is unavailable in Python <3.8,
    # but os.kill accomplishes the same thing.
    os.kill(os.getpid(), signum)


def call_signal_handler(handler, signum, frame):
    """Call the signal handler `handler` with the given arguments `signum`, `frame`"""
    if handler is None:
        raise ValueError("can't trigger a None signal handler")
    elif handler in (signal.SIG_DFL, signal.SIG_IGN):
        # the handler is not callable, so we need to reset the signal and raise it manually.
        with handle_signal(signum, handler):
            raise_signal(signum)
    else:
        handler(signum, frame)
