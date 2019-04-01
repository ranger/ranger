# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

from ranger.colorschemes.default import Default
from ranger.gui.color import bold, BRIGHT, reverse


class Scheme(Default):
    progress_bar_color = 166

    def use(self, context):
        fg, bg, attr = Default.use(self, context)

        if context.directory and not context.marked and not context.link \
                and not context.inactive_pane:
            fg = 165

        elif context.link:
            fg = 122 if context.good or context.in_titlebar else 198

        elif context.in_titlebar and context.hostname:
            fg = 84

        elif context.container:
            fg = 162

        elif context.media:
            if context.image:
                fg = 227
            else:
                fg = 174

        elif context.executable and not \
                any((context.media, context.container,
                     context.fifo, context.socket, context.link)):
            attr |= bold
            fg = 47

        if context.main_column:
            if context.marked and not context.selected:
                attr |= bold
                attr |= reverse
                fg = 214

        return fg, bg, attr
