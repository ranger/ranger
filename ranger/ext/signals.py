# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""An efficient and minimalistic signaling/hook module.

To use this in a class, subclass SignalDispatcher and call
SignalDispatcher.__init__(self) in the __init__ function.  Now you can bind
functions to a signal name (string) by using signal_bind or remove it with
signal_unbind.  Now whenever signal_emit is called with that signal name,
the bound functions are executed in order of priority.

This module supports weak referencing.  This means that if you bind a function
which is later deleted everywhere except in this binding, Python's garbage
collector will remove it from memory.  Activate it with
signal_bind(..., weak=True).  The handlers for such functions are automatically
deleted when trying to call them (in signal_emit), but if they are never
called, they accumulate and should be manually deleted with
signal_garbage_collect().

>>> def test_function(signal):
...     if 'display' in signal:
...         print(signal.display)
...     else:
...         signal.stop()
>>> def temporary_function():
...     print("A temporary function")

>>> sig = SignalDispatcher()

>>> # Test binding and unbinding
>>> handler1 = sig.signal_bind('test', test_function, priority=2)
>>> handler2 = sig.signal_bind('test', temporary_function, priority=1)
>>> sig.signal_emit('test', display="It works!")
It works!
A temporary function
True
>>> # Note that test_function stops the signal when there's no display keyword
>>> sig.signal_emit('test')
False
>>> sig.signal_unbind(handler1)
>>> sig.signal_emit('test')
A temporary function
True
>>> sig.signal_clear()
>>> sig.signal_emit('test')
True

>>> # Bind temporary_function with a weak reference
>>> handler = sig.signal_bind('test', temporary_function, weak=True)
>>> sig.signal_emit('test')
A temporary function
True
>>> # Delete temporary_function.  Its handler is removed too, since it
>>> # was weakly referenced.
>>> del temporary_function
>>> sig.signal_emit('test')
True
"""

from __future__ import (absolute_import, division, print_function)

import weakref
from types import MethodType


class Signal(dict):
    """Signals are passed to the bound functions as an argument.

    They contain the attributes "origin", which is a reference to the
    signal dispatcher, and "name", the name of the signal that was emitted.
    You can call signal_emit with any keyword arguments, which will be
    turned into attributes of this object as well.

    To delete a signal handler from inside a signal, raise a ReferenceError.
    """
    stopped = False

    def __init__(self, **keywords):
        dict.__init__(self, keywords)
        self.__dict__ = self

    def stop(self):
        """ Stop the propagation of the signal to the next handlers.  """
        self.stopped = True


class SignalHandler(object):  # pylint: disable=too-few-public-methods
    """Signal Handlers contain information about a signal binding.

    They are returned by signal_bind() and have to be passed to signal_unbind()
    in order to remove the handler again.

    You can disable a handler without removing it by setting the attribute
    "active" to False.
    """
    active = True

    def __init__(self, signal_name, function, priority, pass_signal):
        self.priority = max(0, min(1, priority))
        self.signal_name = signal_name
        self.function = function
        self.pass_signal = pass_signal


class SignalDispatcher(object):
    """This abstract class handles the binding and emitting of signals."""

    def __init__(self):
        self._signals = dict()

    def signal_clear(self):
        """Remove all signals."""
        for handler_list in self._signals.values():
            for handler in handler_list:
                handler.function = None
        self._signals = dict()

    def signal_bind(self, signal_name, function, priority=0.5, weak=False, autosort=True):
        """Bind a function to the signal.

        signal_name:  Any string to name the signal
        function:  Any function with either one or zero arguments which will be
            called when the signal is emitted.  If it takes one argument, a
            Signal object will be passed to it.
        priority:  Optional, any number.  When signals are emitted, handlers will
            be called in order of priority.  (highest priority first)
        weak:  Use a weak reference of "function" so it can be garbage collected
            properly when it's deleted.

        Returns a SignalHandler which can be used to remove this binding by
        passing it to signal_unbind().
        """
        assert isinstance(signal_name, str)
        assert hasattr(function, '__call__')
        assert hasattr(function, '__code__')
        assert isinstance(priority, (int, float))
        assert isinstance(weak, bool)
        try:
            handlers = self._signals[signal_name]
        except KeyError:
            handlers = self._signals[signal_name] = []
        nargs = function.__code__.co_argcount

        if getattr(function, '__self__', None):
            nargs -= 1
            if weak:
                function = (function.__func__, weakref.proxy(function.__self__))
        elif weak:
            function = weakref.proxy(function)

        handler = SignalHandler(signal_name, function, priority, nargs > 0)
        handlers.append(handler)
        if autosort:
            handlers.sort(
                key=lambda handler: -handler.priority)
        return handler

    # TODO: Do we still use this method? Should we remove it?
    def signal_force_sort(self, signal_name=None):
        """Forces a sorting of signal handlers by priority.

        This is only necessary if you used signal_bind with autosort=False
        after finishing to bind many signals at once.
        """
        if signal_name is None:
            for handlers in self._signals.values():
                handlers.sort(
                    key=lambda handler: -handler.priority)
            return None
        elif signal_name in self._signals:
            self._signals[signal_name].sort(
                key=lambda handler: -handler.priority)
            return None
        return False

    def signal_unbind(self, signal_handler):
        """Removes a signal binding.

        This requires the SignalHandler that has been originally returned by
        signal_bind().
        """
        try:
            handlers = self._signals[
                signal_handler.signal_name]
        except KeyError:
            pass
        else:
            signal_handler.function = None
            try:
                handlers.remove(signal_handler)
            except IndexError:
                pass

    def signal_garbage_collect(self):
        """Remove all handlers with deleted weak references.

        Usually this is not needed; every time you emit a signal, its handlers
        are automatically checked in this way.  However, if you can't be sure
        that a signal is ever emitted AND you keep binding weakly referenced
        functions to the signal, this method should be regularly called to
        avoid memory leaks in self._signals.

        >>> sig = SignalDispatcher()

        >>> # lambda:None is an anonymous function which has no references
        >>> # so it should get deleted immediately
        >>> handler = sig.signal_bind('test', lambda: None, weak=True)
        >>> len(sig._signals['test'])
        1
        >>> # need to call garbage collect so that it's removed from the list.
        >>> sig.signal_garbage_collect()
        >>> len(sig._signals['test'])
        0
        >>> # This demonstrates that garbage collecting is not necessary
        >>> # when using signal_emit().
        >>> handler = sig.signal_bind('test', lambda: None, weak=True)
        >>> sig.signal_emit('another_signal')
        True
        >>> len(sig._signals['test'])
        1
        >>> sig.signal_emit('test')
        True
        >>> len(sig._signals['test'])
        0
        """
        for handler_list in self._signals.values():
            i = len(handler_list)
            while i:
                i -= 1
                handler = handler_list[i]
                try:
                    if isinstance(handler.function, tuple):
                        handler.function[1].__class__  # pylint: disable=pointless-statement
                    else:
                        handler.function.__class__  # pylint: disable=pointless-statement
                except ReferenceError:
                    handler.function = None
                    del handler_list[i]

    def signal_emit(self, signal_name, **kw):
        """Emits a signal and call every function that was bound to that signal.

        You can call this method with any key words.  They will be turned into
        attributes of the Signal object that is passed to the functions.
        If a function calls signal.stop(), no further functions will be called.
        If a function raises a ReferenceError, the handler will be deleted.

        Returns False if signal.stop() was called and True otherwise.
        """
        assert isinstance(signal_name, str)
        if signal_name not in self._signals:
            return True
        handlers = self._signals[signal_name]
        if not handlers:
            return True

        signal = Signal(origin=self, name=signal_name, **kw)

        # propagate
        for handler in tuple(handlers):
            if handler.active:
                try:
                    if isinstance(handler.function, tuple):
                        fnc = MethodType(*handler.function)
                    else:
                        fnc = handler.function
                    if handler.pass_signal:
                        fnc(signal)
                    else:
                        fnc()
                except ReferenceError:
                    handler.function = None
                    handlers.remove(handler)
                if signal.stopped:
                    return False
        return True


if __name__ == '__main__':
    import doctest
    import sys
    sys.exit(doctest.testmod()[0])
