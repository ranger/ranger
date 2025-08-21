"""
Plugin to add a shellcommand linemode to ranger.
⚠️ DANGER: no sanity checks done, be extra careful!
"""

from __future__ import (absolute_import, division, print_function)
from subprocess import CalledProcessError

import ranger.api

from ranger.container.settings import (
    ALLOWED_SETTINGS,
    SIGNAL_PRIORITY_AFTER_SYNC,
    SIGNAL_PRIORITY_SYNC
)
from ranger.core.linemode import LinemodeBase
from ranger.core.shared import SettingsAware, FileManagerAware
from ranger.ext.human_readable import human_readable
from ranger.ext.shell_escape import shell_quote
from ranger.ext.spawn import check_output

HOOK_INIT_OLD = ranger.api.hook_init


def hook_init(fm):
    """
    Hook into ranger startup.
    """

    def _reload():
        """
        Signal handler for option changes to apply
        """
        for tab in fm.tabs.values():
            if tab.thisfile is None:
                continue

            # Purge linemode cache for each matching tab
            if tab.thisfile.linemode == "shellcommand":
                for file in tab.thisdir.files:
                    file.display_data = {}

    # Setup signal handlers
    fm.settings.signal_bind("setopt.preview_files", _reload)
    for suffix in ("", "_format"):
        name = "linemode_shellcommand" + suffix
        # one to reload on setting changes
        fm.settings.signal_bind("setopt." + name, _reload,
                                priority=SIGNAL_PRIORITY_AFTER_SYNC)

        # and this handler to make fm.settings actually store these values
        # which is done in the internal _raw_set_with_signal() function but that
        # is set up in the settings constructor which is invoked before hook_init()
        # so as it's too late for that, manually hook this one up here
        ALLOWED_SETTINGS[name] = str

        # pylint: disable=protected-access
        fm.settings.signal_bind("setopt." + name,
                                fm.settings._raw_set_with_signal,
                                priority=SIGNAL_PRIORITY_SYNC)

    # sensible defaults
    fm.settings.linemode_shellcommand = "stat -c %%F %s"
    fm.settings.linemode_shellcommand_format = "%SIZE% %s"

    # Set up a bunch of key mappings
    fm.execute_console("map MS linemode shellcommand")
    fm.execute_console("map MCI default_linemode shellcommand")

    # some example commands
    fm.execute_console("map MCF chain set linemode_shellcommand fortune -s"
                       + "|tr '\t\n' ' '; set linemode_shellcommand_format %%s")
    fm.execute_console("map MCf set linemode_shellcommand file --brief"
                       + "--mime-type --dereference --special-files %%s")
    fm.execute_console("map MC5 set linemode_shellcommand echo"
                       + "\"$(timeout 1s md5sum %%s | cut -d' ' -f1)\"|grep -v ^$")
    fm.execute_console("map MCd set linemode_shellcommand du -hs %%s | tr '\t' ' '")
    fm.execute_console("map MCs set linemode_shellcommand stat -c %%%%F %%s")

    # string formatting nightmarez ^^
    fm.execute_console("map MC1 set linemode_shellcommand_format %%s")
    fm.execute_console("map MC4 set linemode_shellcommand_format %%SIZE%% %%40.40s")

    # count PDF pages? Sure! : )
    fm.execute_console("map MCp chain default_linemode path=pdf$ shellcommand;"
                       + "set linemode_shellcommand_format %%SIZE%%B %%12s;"
                       + "set linemode_shellcommand COUNT=$(pdfinfo %%s|sed -n \'s/^Pages: *//p\')"
                       + '&& [ -n "$COUNT" ] && echo "$COUNT page pdf"')

    fm.notify("foo", bad=True)
    return HOOK_INIT_OLD(fm)


ranger.api.hook_init = hook_init


@ranger.api.register_linemode
class ShellCommandLinemode(LinemodeBase, SettingsAware, FileManagerAware):
    """
    Provides a shell command linemode.
    """
    name = "shellcommand"

    def filetitle(self, fobj, metadata):
        return fobj.relative_path

    def infostring(self, fobj, metadata):
        str_format = self.settings.linemode_shellcommand_format
        cmd = self.settings.linemode_shellcommand
        cmd = cmd % shell_quote(fobj.path) if "%s" in cmd else cmd
        sizestring = "" if fobj.size is None or fobj.is_directory else human_readable(fobj.size)
        try:
            output = check_output(["sh", "-c", cmd]).strip()
        except CalledProcessError:
            return "PROCESS ERROR"
        return str_format.replace("%SIZE%", sizestring) % (output)
