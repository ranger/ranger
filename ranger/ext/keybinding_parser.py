# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

import copy
import curses.ascii
from collections import OrderedDict

from ranger import PY3

digits = set(map(ord, '0123456789'))  # pylint: disable=invalid-name

# Arbitrary numbers which are not used with curses.KEY_XYZ
ANYKEY, PASSIVE_ACTION, ALT_KEY, QUANT_KEY = range(9001, 9005)

special_keys = OrderedDict([  # pylint: disable=invalid-name
    ('BS', curses.KEY_BACKSPACE),
    ('Backspace', curses.KEY_BACKSPACE),  # overrides <BS> in reversed_special_keys
    ('Backspace2', curses.ascii.DEL),
    ('Delete', curses.KEY_DC),
    ('S-Delete', curses.KEY_SDC),
    ('Insert', curses.KEY_IC),
    ('CR', ord('\n')),
    ('Return', ord('\n')),
    ('Enter', ord('\n')),  # overrides <CR> and <Return> in reversed_special_keys
    ('Space', ord(' ')),
    ('Escape', curses.ascii.ESC),
    ('Esc', curses.ascii.ESC),  # overrides <Escape> in reversed_special_keys
    ('Down', curses.KEY_DOWN),
    ('Up', curses.KEY_UP),
    ('Left', curses.KEY_LEFT),
    ('Right', curses.KEY_RIGHT),
    ('PageDown', curses.KEY_NPAGE),
    ('PageUp', curses.KEY_PPAGE),
    ('Home', curses.KEY_HOME),
    ('End', curses.KEY_END),
    ('Tab', ord('\t')),
    ('S-Tab', curses.KEY_BTAB),
    ('lt', ord('<')),
    ('gt', ord('>')),
])
named_special_keys = tuple(special_keys.keys())  # pylint: disable=invalid-name
special_keys_uncased = {}  # pylint: disable=invalid-name
very_special_keys = {  # pylint: disable=invalid-name
    'Alt': ALT_KEY,
    'any': ANYKEY,
    'bg': PASSIVE_ACTION,
    'allow_quantifiers': QUANT_KEY,
}


def _uncase_special_key(string):
    """Uncase a special key

    >>> _uncase_special_key('Esc')
    'esc'

    >>> _uncase_special_key('C-X')
    'c-x'
    >>> _uncase_special_key('C-x')
    'c-x'

    >>> _uncase_special_key('A-X')
    'a-X'
    >>> _uncase_special_key('A-x')
    'a-x'
    """
    uncased = string.lower()
    if len(uncased) == 3 and (uncased.startswith('a-') or uncased.startswith('m-')):
        uncased = '%s-%s' % (uncased[0], string[-1])
    return uncased


def _special_keys_init():
    for key, val in tuple(special_keys.items()):
        special_keys['M-' + key] = (ALT_KEY, val)
        special_keys['A-' + key] = (ALT_KEY, val)  # overrides <M-*> in reversed_special_keys

    for char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_!{}[],./':
        special_keys['M-' + char] = (ALT_KEY, ord(char))
        special_keys['A-' + char] = (ALT_KEY, ord(char))  # overrides <M-*> in reversed_special_keys

    # We will need to reorder the keys of special_keys below.
    # For example, <C-j> will override <Enter> in reverse_special_keys,
    # this makes construct_keybinding(parse_keybinding('<CR>')) == '<C-j>'
    for char in 'abcdefghijklmnopqrstuvwxyz_':
        special_keys['C-' + char] = ord(char) - 96

    special_keys['C-Space'] = 0

    for n in range(64):
        special_keys['F' + str(n)] = curses.KEY_F0 + n

    special_keys.update(very_special_keys)

    # Reorder reorder the keys of special_keys.
    for key in named_special_keys:
        val = special_keys[key]
        del special_keys[key]
        special_keys[key] = val  # Python 3 added OrderedDict.move_to_end(key, last=True)

    for key, val in special_keys.items():
        special_keys_uncased[_uncase_special_key(key)] = val


_special_keys_init()
del _special_keys_init, very_special_keys, named_special_keys
reversed_special_keys = OrderedDict([  # pylint: disable=invalid-name
    (v, k) for k, v in special_keys.items()
])


def parse_keybinding(obj):  # pylint: disable=too-many-branches
    r"""Translate a keybinding to a sequence of integers
    The letter case of special keys in the keybinding string will be ignored.

    >>> out = tuple(parse_keybinding('lol<CR>'))
    >>> out
    (108, 111, 108, 10)
    >>> out == (ord('l'), ord('o'), ord('l'), ord('\n'))
    True

    >>> out = tuple(parse_keybinding('x<A-Left>'))
    >>> out
    (120, 9003, 260)
    >>> out == (ord('x'), ALT_KEY, curses.KEY_LEFT)
    True
    """
    assert isinstance(obj, (tuple, int, str))
    if isinstance(obj, tuple):
        for char in obj:
            yield char
    elif isinstance(obj, int):
        yield obj
    else:  # pylint: disable=too-many-nested-blocks
        in_brackets = False
        bracket_content = []
        for char in obj:
            if in_brackets:
                if char == '>':
                    in_brackets = False
                    string = ''.join(bracket_content)
                    try:
                        keys = special_keys_uncased[_uncase_special_key(string)]
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


def key_to_string(key):
    if key in range(33, 127):
        return chr(key)
    if key in reversed_special_keys:
        return '<%s>' % reversed_special_keys[key]
    return '<%s>' % str(key)


def construct_keybinding(keys):
    """Does the reverse of parse_keybinding

    >>> construct_keybinding(parse_keybinding('lol<CR>'))
    'lol<Enter>'

    >>> construct_keybinding(parse_keybinding('x<A-Left>'))
    'x<A-Left>'

    >>> construct_keybinding(parse_keybinding('x<Alt><Left>'))
    'x<A-Left>'
    """
    try:
        keys = tuple(keys)
    except TypeError:
        assert isinstance(keys, int)
        keys = (keys,)
    strings = []
    alt_key_on = False
    for key in keys:
        if key == ALT_KEY:
            alt_key_on = True
            continue
        if alt_key_on:
            try:
                strings.append('<%s>' % reversed_special_keys[(ALT_KEY, key)])
            except KeyError:
                strings.extend(map(key_to_string, (ALT_KEY, key)))
        else:
            strings.append(key_to_string(key))
        alt_key_on = False

    return ''.join(strings)


class KeyMaps(dict):

    def __init__(self, keybuffer=None):
        dict.__init__(self)
        self.keybuffer = keybuffer
        self.used_keymap = None

    def use_keymap(self, keymap_name):
        self.keybuffer.keymap = self.get(keymap_name, {})
        if self.used_keymap != keymap_name:
            self.used_keymap = keymap_name
            self.keybuffer.clear()

    def _clean_input(self, context, keys):
        try:
            pointer = self[context]
        except KeyError:
            self[context] = pointer = {}
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
                    pointer[key] = pointer = {}
            except KeyError:
                pointer[key] = pointer = {}
        pointer[last_key] = leaf

    def copy(self, context, source, target):
        clean_source, pointer = self._clean_input(context, source)
        if not source:
            return
        for key in clean_source:
            try:
                pointer = pointer[key]
            except KeyError:
                raise KeyError("Tried to copy the keybinding `%s',"
                               " but it was not found." % source)
        self.bind(context, target, copy.deepcopy(pointer))

    def unbind(self, context, keys):
        keys, pointer = self._clean_input(context, keys)
        if not keys:
            return
        self._unbind_traverse(pointer, keys)

    @staticmethod
    def _unbind_traverse(pointer, keys, pos=0):
        if keys[pos] not in pointer:
            return
        if len(keys) > pos + 1 and isinstance(pointer, dict):
            KeyMaps._unbind_traverse(pointer[keys[pos]], keys, pos=pos + 1)
            if not pointer[keys[pos]]:
                del pointer[keys[pos]]
        elif len(keys) == pos + 1:
            try:
                del pointer[keys[pos]]
            except KeyError:
                pass
            try:
                keys.pop()
            except IndexError:
                pass


class KeyBuffer(object):  # pylint: disable=too-many-instance-attributes
    any_key = ANYKEY
    passive_key = PASSIVE_ACTION
    quantifier_key = QUANT_KEY
    excluded_from_anykey = [curses.ascii.ESC]

    def __init__(self, keymap=None):
        # Pylint recommends against calling __init__ explicitly and requires
        # certain fields to be declared in __init__ so we set those to None.
        # For some reason list fields don't have the same requirement.
        self.pointer = None
        self.result = None
        self.quantifier = None
        self.finished_parsing_quantifier = None
        self.finished_parsing = None
        self.parse_error = None

        self.keymap = keymap
        self.clear()

    def clear(self):
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

    def add(self, key):
        self.keys.append(key)
        self.result = None
        if not self.finished_parsing_quantifier and key in digits:
            if self.quantifier is None:
                self.quantifier = 0
            self.quantifier = self.quantifier * 10 + key - 48  # (48 = ord('0'))
        else:
            self.finished_parsing_quantifier = True

            moved = True
            if key in self.pointer:
                self.pointer = self.pointer[key]
            elif self.any_key in self.pointer and \
                    key not in self.excluded_from_anykey:
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
        return construct_keybinding(self.keys)


if __name__ == '__main__':
    import doctest
    import sys
    sys.exit(doctest.testmod()[0])
