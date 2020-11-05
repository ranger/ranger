# Tested with ranger 1.7.2
#
# This plugin creates a bunch of keybindings used to mount and unmount
# the devices using pmount(1).
#
# (multiple partitions): alt+m <letter> <digit>  : mount /dev/sd<letter><digit>
# (one partition):       alt+m <letter>          : mount /dev/sd<letter>1
# (no partitions):       alt+m <letter>          : mount /dev/sd<letter>
#
# (multiple partitions): alt+M <letter> <digit>  : unmount /dev/sd<letter><digit>
# (one partition):       alt+M <letter>          : unmount /dev/sd<letter>1
# (no partitions):       alt+M <letter>          : unmount /dev/sd<letter>
#
# alt+n : list the devices

from __future__ import (absolute_import, division, print_function)

import subprocess
import ranger.api

MOUNT_KEY = '<alt>m'
UMOUNT_KEY = '<alt>M'
LIST_MOUNTS_KEY = '<alt>n'
HOOK_INIT_OLD = ranger.api.hook_init


def hook_init(fm):
    fm.execute_console("map {key} shell -p lsblk".format(key=LIST_MOUNTS_KEY))

    diskcmd = "lsblk -lno NAME | awk '!/[1-9]/ {sub(/sd/, \"\"); print}'"
    disks = subprocess.check_output(
        diskcmd, shell=True).decode('utf-8').replace('\r', '').replace('\n', '')

    for disk in disks:
        partcmd = "lsblk -lno NAME /dev/sd{0} | sed 's/sd{0}//' | tail -n 1".format(disk)

        try:
            numparts = int(subprocess.check_output(
                partcmd, shell=True).decode('utf-8').replace('\r', '').replace('\n', ''))
        except ValueError:
            numparts = 0

        if numparts == 0:
            # no partition, mount the whole device
            fm.execute_console("map {key}{0} chain shell pmount sd{0}; cd /media/sd{0}".format(
                disk, key=MOUNT_KEY))
            fm.execute_console("map {key}{0} chain cd; chain shell pumount sd{0}".format(
                disk, key=UMOUNT_KEY))

        elif numparts == 1:
            # only one partition, mount the partition
            fm.execute_console(
                "map {key}{0} chain shell pmount sd{0}1; cd /media/sd{0}1".format(
                    disk, key=MOUNT_KEY))
            fm.execute_console("map {key}{0} chain cd; shell pumount sd{0}1".format(
                disk, key=UMOUNT_KEY))

        else:
            # use range start 1, /dev/sd{device}0 doesn't exist
            for part in range(1, numparts + 1):
                fm.execute_console(
                    "map {key}{0}{1} chain shell pmount sd{0}{1}; cd /media/sd{0}{1}".format(
                        disk, part, key=MOUNT_KEY))
                fm.execute_console("map {key}{0}{1} chain cd; shell pumount sd{0}{1}".format(
                    disk, part, key=UMOUNT_KEY))

    return HOOK_INIT_OLD(fm)


ranger.api.hook_init = hook_init
