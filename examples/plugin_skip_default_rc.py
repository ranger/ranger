# This plugin inhibits the loading of the default rc.conf.  This serves to
# speed up starting time by avoiding to load rc.conf twice if you have a full
# copy of it in ~/.config/ranger.
#
# Don't use this if you have a supplementary rc.conf or no rc.conf at all, or
# you will end up without key bindings and options.

import ranger.core.main
ranger.core.main.load_default_config = False
