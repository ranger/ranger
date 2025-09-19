# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""FIXME: a lot of effort for a bit of fudging of stat objects"""

from __future__ import (absolute_import, division, print_function)

from logging import getLogger
from os import stat_result
from time import ctime

from ranger.core.shared import SettingsAware

LOG = getLogger(__name__)


def fudge_symlink_stat(link_stat, target_stat):
    settings = SettingsAware.settings

    stat_dict = {
        k: getattr(target_stat, k) for k in target_stat.__class__.__dict__
        if k.startswith("st_")
    }

    for entry in settings.fudge_symlink_stat:
        if entry in ("", "none", "False"):
            LOG.info("fudge_symlink_stat set to '%s', not fudging the stat", entry)
            return target_stat

        attr = "st_" + entry
        LOG.debug('%s "%s" %s -> %s', __name__, entry, stat_dict[attr], getattr(link_stat, attr))
        LOG.debug('%s "%s" %s -> %s', __name__, entry, ctime(stat_dict[attr]),
                  ctime(getattr(link_stat, attr)))
        stat_dict[attr] = getattr(link_stat, attr)

    # reconstruct stat object from tempered dict
    return stat_result(list(stat_dict.values())[:10])
