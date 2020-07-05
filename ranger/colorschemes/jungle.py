# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

from ranger.colorschemes.default import Default
from ranger.gui.color import green, red, blue, bold


class Scheme(Default):
    progress_bar_color = green

    def use(self, context):
        fg, bg, attr = Default.use(self, context)

        if context.directory and not context.marked and not context.link \
                and not context.inactive_pane:
            fg = self.progress_bar_color

        if context.line_number and not context.selected:
            fg = self.progress_bar_color
            attr &= ~bold

        if context.in_titlebar and context.hostname:
            fg = red if context.bad else blue

        return fg, bg, attr
