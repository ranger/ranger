# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from ranger.gui.colorscheme import ColorScheme
from ranger.gui.color import *


class Snow(ColorScheme):

    def use(self, context):
        fg, bg, attr = default_colors

        if context.reset:
            pass

        elif context.in_browser:
            if context.selected:
                attr = reverse
            if context.directory:
                attr |= bold

        elif context.highlight:
            attr |= reverse

        elif context.in_titlebar and context.tab and context.good:
            attr |= reverse

        elif context.in_statusbar:
            if context.loaded:
                attr |= reverse
            if context.marked:
                attr |= reverse

        elif context.in_taskview:
            if context.selected:
                attr |= bold
            if context.loaded:
                attr |= reverse

        return fg, bg, attr
