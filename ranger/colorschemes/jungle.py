# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from ranger.gui.color import blue, green, red
from ranger.colorschemes.default import Default


class Scheme(Default):
    progress_bar_color = green

    def use(self, context):
        fg, bg, attr = Default.use(self, context)

        if context.directory and not context.marked and not context.link \
                and not context.inactive_pane:
            fg = green

        if context.in_titlebar and context.hostname:
            fg = red if context.bad else blue

        return fg, bg, attr
