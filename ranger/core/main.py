from ranger.core.status import Status
from ranger.core.gui import ui
from ranger.core.fs import File, Directory
from ranger.ext.shell_escape import shell_escape
import os
import sys
import curses
import locale

def main():
	try: locale.setlocale(locale.LC_ALL, '')
	except: print("Warning: Unable to set locale.  Expect encoding problems.")
	status = Status()
	status.cd(sys.argv[1], bookmark=False)
	settingsfile = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'settings.py')
	settings = compile(open(settingsfile).read(), settingsfile, 'exec')
	global status
	exec(settings, globals())
	try:
		status.stdscr = curses.initscr()
		load_status(status)
		status.curses_on()
		ui(status)
	finally:
		status.curses_off()
		save_status(status)


def load_status(status):
	try:
		pointer = os.environ['RANGER_POINTER']
	except:
		pass
	else:
		dir = status.get_dir(os.path.dirname(pointer))
		dir.select_filename(pointer)
	status.sync_pointer()


def save_status(status):
	from ranger.core.communicate import echo
	try:
		echo(status.cwd.path, 'last_dir')
		echo(status.cwd.current_file.path, 'last_pointer')
		echo(str(status.cwd.scroll_begin), 'last_scroll_start')
		echo('\n'.join(status.selection), 'last_selection')
	except:
		pass
