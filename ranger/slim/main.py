import ranger.slim.settings
from ranger.slim.status import Status
from ranger.slim.gui import ui
from ranger.slim.fs import File, Directory
import curses

def main():
	status = Status()
	status.cd(".")
	status.keymap = ranger.slim.settings.keys
	status.rows = ranger.slim.settings.rows
	curses.wrapper(ui, status)
