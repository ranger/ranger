#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function)

import sys
import time

sys.path.insert(0, '../..')
sys.path.insert(0, '.')


def main():
    import ranger.container.directory
    import ranger.core.shared
    import ranger.container.settings
    import ranger.core.fm
    from ranger.ext.openstruct import OpenStruct
    ranger.args = OpenStruct()
    ranger.args.clean = True
    ranger.args.debug = False

    settings = ranger.container.settings.Settings()
    ranger.core.shared.SettingsAware.settings_set(settings)
    fm = ranger.core.fm.FM()
    ranger.core.shared.FileManagerAware.fm_set(fm)

    time1 = time.time()
    fm.initialize()
    try:
        usr = ranger.container.directory.Directory('/usr')
        usr.load_content(schedule=False)
        for fileobj in usr.files:
            if fileobj.is_directory:
                fileobj.load_content(schedule=False)
    finally:
        fm.destroy()
    time2 = time.time()
    print("%dms" % ((time2 - time1) * 1000))


if __name__ == '__main__':
    main()
