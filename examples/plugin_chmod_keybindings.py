# This plugin serves as an example for adding key bindings through a plugin.
# It could replace the ten lines in the rc.conf that create the key bindings
# for the "chmod" command.

import ranger.core.fm
old_init_hook = ranger.core.fm.init_hook

def init_hook(fm):
	old_init_hook(fm)

	# Generate key bindings for the chmod command
	command = "map {0}{1}{2} shell -d chmod {1}{0}{2} %s"
	for	mode in list('ugoa') + '':
		for	perm in "rwxXst":
			fm.execute_console(command.format('-', mode, perm))
			fm.execute_console(command.format('+', mode, perm))

ranger.core.fm.init_hook = init_hook
