# Compatible with ranger 1.6.0 through ranger 1.7.*
#
# This plugin serves as an example for adding key bindings through a plugin.
# It could replace the ten lines in the rc.conf that create the key bindings
# for the "chmod" command.

import ranger.api
old_hook_init = ranger.api.hook_init


def hook_init(fm):
    old_hook_init(fm)

    # Generate key bindings for the chmod command
    command = "map {0}{1}{2} shell -d chmod {1}{0}{2} %s"
    for mode in list('ugoa') + ['']:
        for perm in "rwxXst":
            fm.execute_console(command.format('-', mode, perm))
            fm.execute_console(command.format('+', mode, perm))


ranger.api.hook_init = hook_init
