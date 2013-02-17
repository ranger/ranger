# -*- coding: utf-8 -*-

from ranger.gui.displayable import Displayable

class Widget(Displayable):
    """
    The Widget class defines no methods and only exists for
    classification of widgets.
    """
    vcsfilestatus_symb = {'conflict':  ('X', ["vcsconflict"]),
                  'untracked': ('+', ["vcschanged"]),
                  'deleted':   ('-', ["vcschanged"]),
                  'changed':   ('*', ["vcschanged"]),
                  'staged':    ('*', ["vcsstaged"]),
                  'ignored':   ('·', ["vcsignored"]),
                  'sync':      ('√', ["vcssync"]),
                  'none':      (' ', []),
                  'unknown':   ('?', ["vcsunknown"])}

    vcsremotestatus_symb = {'none':     (' ',  []),
                'sync':     ('=', ["vcssync"]),
                'behind':   ('<', ["vcsbehind"]),
                'ahead':    ('>', ["vcsahead"]),
                'diverged': ('Y', ["vcsdiverged"]),
                'unknown':  ('?', ["vcsunknown"])}
