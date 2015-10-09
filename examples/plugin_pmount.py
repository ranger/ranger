# Tested with ranger 1.7.2
#
# This plugin creates a bunch of keybindings used to mount and unmount
# the devices using pmount(1).
#
# alt+m       <letter>            <digit>: mount /dev/sd<letter><digit>
# alt+m       <uppercase letter>         : mount /dev/sd<letter>
# alt+shift+m <letter>            <digit>: unmount /dev/sd<letter><digit>
# alt+shift+m <uppercase letter>         : unmount /dev/sd<letter>
# alt+shift+n                            : list the devices

import ranger.api

MOUNT_KEY = '<alt>m'
UMOUNT_KEY = '<alt>M'
LIST_MOUNTS_KEY = '<alt>N'

old_hook_init = ranger.api.hook_init
def hook_init(fm):
    try:
        fm.execute_console("map {key} shell -p lsblk".format(key=LIST_MOUNTS_KEY))
        for disk in "abcdefgh":
            fm.execute_console("map {key}{0} chain shell pmount sd{1}; cd /media/sd{1}".format(disk.upper(), disk, key=MOUNT_KEY))
            fm.execute_console("map {key}{0} chain cd; chain shell pumount sd{1}".format(disk.upper(), disk, key=UMOUNT_KEY))
            for part in "123456789":
                fm.execute_console("map {key}{0}{1} chain shell pmount sd{0}{1}; cd /media/sd{0}{1}".format(disk, part, key=MOUNT_KEY))
                fm.execute_console("map {key}{0}{1} chain cd; shell pumount sd{0}{1}".format(disk, part, key=UMOUNT_KEY))
    finally:
        return old_hook_init(fm)
ranger.api.hook_init = hook_init
