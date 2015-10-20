# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""Colorschemes define colors for specific contexts.

Generally, this works by passing a set of keywords (strings) to
the colorscheme.get() method to receive the tuple (fg, bg, attr).
fg, bg are the foreground and background colors and attr is the attribute.
The values are specified in ranger.gui.color.

A colorscheme must...

1. be inside either of these directories:
~/.config/ranger/colorschemes/
path/to/ranger/colorschemes/

2. be a subclass of ranger.gui.colorscheme.ColorScheme

3. implement a use(self, context) method which returns (fg, bg, attr).
context is a struct which contains all entries of CONTEXT_KEYS,
associated with either True or False.

Define which colorscheme in your settings (e.g. ~/.config/ranger/rc.conf):
set colorscheme yourschemename
"""

import os.path
from curses import color_pair

import ranger
from ranger.gui.color import get_color
from ranger.gui.context import Context
from ranger.core.main import allow_access_to_confdir
from ranger.ext.cached_function import cached_function
from ranger.ext.iter_tools import flatten

class ColorScheme(object):
    """This is the class that colorschemes must inherit from.

    it defines the get() method, which returns the color tuple
    which fits to the given keys.
    """

    @cached_function
    def get(self, *keys):
        """Returns the (fg, bg, attr) for the given keys.

        Using this function rather than use() will cache all
        colors for faster access.
        """
        context = Context(keys)
        color = self.use(context)
        if len(color) != 3 or not all(isinstance(value, int) \
                for value in color):
            raise ValueError("Bad Value from colorscheme.  Need "
                "a tuple of (foreground_color, background_color, attribute).")
        return color

    @cached_function
    def get_attr(self, *keys):
        """Returns the curses attribute for the specified keys

        Ready to use for curses.setattr()
        """
        fg, bg, attr = self.get(*flatten(keys))
        return attr | color_pair(get_color(fg, bg))

    def use(self, context):
        """Use the colorscheme to determine the (fg, bg, attr) tuple.

        Override this method in your own colorscheme.
        """
        return (-1, -1, 0)

def _colorscheme_name_to_class(signal):
    # Find the colorscheme.  First look in ~/.config/ranger/colorschemes,
    # then at RANGERDIR/colorschemes.  If the file contains a class
    # named Scheme, it is used.  Otherwise, an arbitrary other class
    # is picked.
    if isinstance(signal.value, ColorScheme): return

    if not signal.value:
        signal.value = 'default'

    scheme_name = signal.value
    usecustom = not ranger.arg.clean

    def exists(colorscheme):
        return os.path.exists(colorscheme + '.py') or os.path.exists(colorscheme + '.pyc')

    def is_scheme(x):
        try:
            return issubclass(x, ColorScheme)
        except:
            return False

    # create ~/.config/ranger/colorschemes/__init__.py if it doesn't exist
    if usecustom:
        if os.path.exists(signal.fm.confpath('colorschemes')):
            initpy = signal.fm.confpath('colorschemes', '__init__.py')
            if not os.path.exists(initpy):
                open(initpy, 'a').close()

    if usecustom and \
            exists(signal.fm.confpath('colorschemes', scheme_name)):
        scheme_supermodule = 'colorschemes'
    elif exists(signal.fm.relpath('colorschemes', scheme_name)):
        scheme_supermodule = 'ranger.colorschemes'
        usecustom = False
    else:
        scheme_supermodule = None  # found no matching file.

    if scheme_supermodule is None:
        if signal.previous and isinstance(signal.previous, ColorScheme):
            signal.value = signal.previous
        else:
            signal.value = ColorScheme()
        raise Exception("Cannot locate colorscheme `%s'" % scheme_name)
    else:
        if usecustom: allow_access_to_confdir(ranger.arg.confdir, True)
        scheme_module = getattr(__import__(scheme_supermodule,
                globals(), locals(), [scheme_name], 0), scheme_name)
        if usecustom: allow_access_to_confdir(ranger.arg.confdir, False)
        if hasattr(scheme_module, 'Scheme') \
                and is_scheme(scheme_module.Scheme):
            signal.value = scheme_module.Scheme()
        else:
            for var in scheme_module.__dict__.values():
                if var != ColorScheme and is_scheme(var):
                    signal.value = var()
                    break
            else:
                raise Exception("The module contains no valid colorscheme!")

def get_all_colorschemes():
    colorschemes = set()
    # Load colorscheme names from main ranger/colorschemes dir
    for item in os.listdir(ranger.RANGERDIR + '/colorschemes'):
        if not item.startswith('__'):
            colorschemes.add(item.rsplit('.', 1)[0])
    # Load colorscheme names from ~/.config/ranger/colorschemes if dir exists
    if os.path.isdir(os.path.expanduser(ranger.CONFDIR + '/colorschemes')):
        for item in os.listdir(os.path.expanduser(
                ranger.CONFDIR + '/colorschemes')):
            if not item.startswith('__'):
                colorschemes.add(item.rsplit('.', 1)[0])
    return list(sorted(colorschemes))
