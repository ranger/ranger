# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

from ranger.colorschemes.default import Default
from ranger.gui.color import green, red, blue, bold


class Scheme(Default):
    progress_bar_color = green

    Default.colors['in_browser']['directory'] = {'fg': green, 'attr': bold}
    Default.colors['in_titlebar']['hostname']['default'] = {'fg': blue}
    Default.colors['in_titlebar']['hostname']['bad'] = {'fg': red}
