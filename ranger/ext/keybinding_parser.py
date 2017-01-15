# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, print_function)

import sys
import copy
import curses.ascii

PY3 = sys.version_info[0] >= 3
digits = set(range(ord('0'), ord('9') + 1))  # pylint: disable=invalid-name

# Arbitrary numbers which are not used with curses.KEY_XYZ
ANYKEY, PASSIVE_ACTION, ALT_KEY, QUANT_KEY = range(9001, 9005)

special_keys = {  # pylint: disable=invalid-name
    'bs': curses.KEY_BACKSPACE,
    'backspace': curses.KEY_BACKSPACE,
    'backspace2': curses.ascii.DEL,
    'delete': curses.KEY_DC,
    's-delete': curses.KEY_SDC,
    'insert': curses.KEY_IC,
    'cr': ord("\n"),
    'enter': ord("\n"),
    'return': ord("\n"),
    'space': ord(" "),
    'esc': curses.ascii.ESC,
    'escape': curses.ascii.ESC,
    'down': curses.KEY_DOWN,
    'up': curses.KEY_UP,
    'left': curses.KEY_LEFT,
    'right': curses.KEY_RIGHT,
    'pagedown': curses.KEY_NPAGE,
    'pageup': curses.KEY_PPAGE,
    'home': curses.KEY_HOME,
    'end': curses.KEY_END,
    'tab': ord('\t'),
    's-tab': curses.KEY_BTAB,
    'lt': ord('<'),
    'gt': ord('>'),
}

very_special_keys = {  # pylint: disable=invalid-name
    'any': ANYKEY,
    'alt': ALT_KEY,
    'bg': PASSIVE_ACTION,
    'allow_quantifiers': QUANT_KEY,
}


def special_keys_init():
    for key, val in tuple(special_keys.items()):
        special_keys['a-' + key] = (ALT_KEY, val)

    for char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_!{}':
        special_keys['a-' + char] = (ALT_KEY, ord(char))

    for char in 'abcdefghijklmnopqrstuvwxyz_':
        special_keys['c-' + char] = ord(char) - 96

    special_keys['c-space'] = 0

    for n in range(64):
        special_keys['f' + str(n)] = curses.KEY_F0 + n


special_keys_init()

special_keys.update(very_special_keys)
del very_special_keys
reversed_special_keys = dict(  # pylint: disable=invalid-name
    (v, k) for k, v in special_keys.items())


def parse_keybinding(obj):  # pylint: disable=too-many-branches
    """Translate a keybinding to a sequence of integers

    >>> tuple(parse_keybinding("lol<CR>"))
    (108, 111, 108, 10)

    >>> out = tuple(parse_keybinding("x<A-Left>"))
    >>> out  # it's kind of dumb that you can't test for constants...
    (120, 9003, 260)
    >>> out[0] == ord('x')
    True
    >>> out[1] == ALT_KEY
    True
    >>> out[2] == curses.KEY_LEFT
    True
    """
    assert isinstance(obj, (tuple, int, str))
    if isinstance(obj, tuple):
        for char in obj:
            yield char
    elif isinstance(obj, int):
        yield obj
    elif isinstance(obj, str):  # pylint: disable=too-many-nested-blocks
        in_brackets = False
        bracket_content = []
        for char in obj:
            if in_brackets:
                if char == '>':
                    in_brackets = False
                    string = ''.join(bracket_content).lower()
                    try:
                        keys = special_keys[string]
                        for key in keys:
                            yield key
                    except KeyError:
                        if string.isdigit():
                            yield int(string)
                        else:
                            yield ord('<')
                            for bracket_char in bracket_content:
                                yield ord(bracket_char)
                            yield ord('>')
                    except TypeError:
                        yield keys  # it was no tuple, just an int
                else:
                    bracket_content.append(char)
            else:
                if char == '<':
                    in_brackets = True
                    bracket_content = []
                else:
                    yield ord(char)
        if in_brackets:
            yield ord('<')
            for char in bracket_content:
                yield ord(char)


def construct_keybinding(iterable):
    """Does the reverse of parse_keybinding"""
    return ''.join(key_to_string(c) for c in iterable)


def key_to_string(key):
    if key in range(33, 127):
        return chr(key)
    if key in reversed_special_keys:
        return "<%s>" % reversed_special_keys[key]
    return "<%s>" % str(key)


def _unbind_traverse(pointer, keys, pos=0):
    if keys[pos] not in pointer:
        return
    if len(keys) > pos + 1 and isinstance(pointer, dict):
        _unbind_traverse(pointer[keys[pos]], keys, pos=pos + 1)
        if not pointer[keys[pos]]:
            del pointer[keys[pos]]
    elif len(keys) == pos + 1:
        try:
            del pointer[keys[pos]]
            keys.pop()
        except Exception:
            pass


class KeyMaps(dict):

    def __init__(self, keybuffer=None):
        dict.__init__(self)
        self.keybuffer = keybuffer
        self.used_keymap = None

    def use_keymap(self, keymap_name):
        self.keybuffer.keymap = self.get(keymap_name, dict())
        if self.used_keymap != keymap_name:
            self.used_keymap = keymap_name
            self.keybuffer.clear()

    def _clean_input(self, context, keys):
        try:
            pointer = self[context]
        except Exception:
            self[context] = pointer = dict()
        if PY3:
            keys = keys.encode('utf-8').decode('latin-1')
        return list(parse_keybinding(keys)), pointer

    def bind(self, context, keys, leaf):
        keys, pointer = self._clean_input(context, keys)
        if not keys:
            return
        last_key = keys[-1]
        for key in keys[:-1]:
            try:
                if isinstance(pointer[key], dict):
                    pointer = pointer[key]
                else:
                    pointer[key] = pointer = dict()
            except Exception:
                pointer[key] = pointer = dict()
        pointer[last_key] = leaf

    def copy(self, context, source, target):
        clean_source, pointer = self._clean_input(context, source)
        if not source:
            return
        for key in clean_source:
            try:
                pointer = pointer[key]
            except Exception:
                raise KeyError("Tried to copy the keybinding `%s',"
                               " but it was not found." % source)
        self.bind(context, target, copy.deepcopy(pointer))

    def unbind(self, context, keys):
        keys, pointer = self._clean_input(context, keys)
        if not keys:
            return
        _unbind_traverse(pointer, keys)


class KeyBuffer(object):  # pylint: disable=too-many-instance-attributes
    any_key = ANYKEY
    passive_key = PASSIVE_ACTION
    quantifier_key = QUANT_KEY
    exclude_from_anykey = [27]

    def __init__(self, keymap=None):
        self.keymap = keymap
        self.keys = []
        self.wildcards = []
        self.pointer = self.keymap
        self.result = None
        self.quantifier = None
        self.finished_parsing_quantifier = False
        self.finished_parsing = False
        self.parse_error = False

        if self.keymap and self.quantifier_key in self.keymap:
            if self.keymap[self.quantifier_key] == 'false':
                self.finished_parsing_quantifier = True

    def clear(self):
        self.__init__(self.keymap)

    def add(self, key):
        self.keys.append(key)
        self.result = None
        if not self.finished_parsing_quantifier and key in digits:
            if self.quantifier is None:
                self.quantifier = 0
            self.quantifier = self.quantifier * 10 + key - 48  # (48 = ord(0))
        else:
            self.finished_parsing_quantifier = True

            moved = True
            if key in self.pointer:
                self.pointer = self.pointer[key]
            elif self.any_key in self.pointer and \
                    key not in self.exclude_from_anykey:
                self.wildcards.append(key)
                self.pointer = self.pointer[self.any_key]
            else:
                moved = False

            if moved:
                if isinstance(self.pointer, dict):
                    if self.passive_key in self.pointer:
                        self.result = self.pointer[self.passive_key]
                else:
                    self.result = self.pointer
                    self.finished_parsing = True
            else:
                self.finished_parsing = True
                self.parse_error = True

    def __str__(self):
        return "".join(key_to_string(c) for c in self.keys)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
