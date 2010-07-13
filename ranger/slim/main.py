import ranger.slim.settings
from ranger.slim.status import Status
from ranger.slim.gui import ui
from ranger.slim.fs import File, Directory
import os
import curses

def main():
	status = Status()
	status.cd(".")
	status.keymap = ranger.slim.settings.keys
	status.rows = ranger.slim.settings.rows
	status.get_color = ranger.slim.settings.get_color
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
	status.sync()

def save_status(status):
	from ranger.slim.communicate import echo
	echo(status.cwd.path, 'last_dir')
	echo(status.cwd.current_file.path, 'last_pointer')
	echo(str(status.cwd.scroll_begin), 'last_scroll_start')
