# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""The File Manager, putting the pieces together"""

from time import time
from collections import deque
import mimetypes
import os.path
import pwd
import socket
import stat
import sys

import ranger.api
from ranger.core.actions import Actions
from ranger.core.tab import Tab
from ranger.container import settings
from ranger.container.tags import Tags, TagsDummy
from ranger.gui.ui import UI
from ranger.container.bookmarks import Bookmarks
from ranger.core.runner import Runner
from ranger.ext.img_display import *
from ranger.core.metadata import MetadataManager
from ranger.ext.rifle import Rifle
from ranger.container.directory import Directory
from ranger.ext.signals import SignalDispatcher
from ranger import __version__
from ranger.core.loader import Loader


class FM(Actions, SignalDispatcher):
    input_blocked = False
    input_blocked_until = 0
    mode = 'normal'  # either 'normal' or 'visual'.
    search_method = 'ctime'

    _previous_selection = None
    _visual_reverse = False
    _visual_start = None
    _visual_start_pos = None

    def __init__(self, ui=None, bookmarks=None, tags=None, paths=['.']):
        """Initialize FM."""
        Actions.__init__(self)
        SignalDispatcher.__init__(self)
        if ui is None:
            self.ui = UI()
        else:
            self.ui = ui
        self.start_paths = paths
        self.directories = dict()
        self.log = deque(maxlen=1000)
        self.bookmarks = bookmarks
        self.current_tab = 1
        self.tabs = {}
        self.tags = tags
        self.restorable_tabs = deque([], ranger.MAX_RESTORABLE_TABS)
        self.py3 = sys.version_info >= (3, )
        self.previews = {}
        self.default_linemodes = deque()
        self.loader = Loader()
        self.copy_buffer = set()
        self.do_cut = False
        self.metadata = MetadataManager()

        try:
            self.username = pwd.getpwuid(os.geteuid()).pw_name
        except Exception:
            self.username = 'uid:' + str(os.geteuid())
        self.hostname = socket.gethostname()
        self.home_path = os.path.expanduser('~')

        self.log.appendleft('ranger {0} started! Process ID is {1}.'
                .format(__version__, os.getpid()))
        self.log.appendleft('Running on Python ' + sys.version.replace('\n', ''))

        mimetypes.knownfiles.append(os.path.expanduser('~/.mime.types'))
        mimetypes.knownfiles.append(self.relpath('data/mime.types'))
        self.mimetypes = mimetypes.MimeTypes()

    def initialize(self):
        """If ui/bookmarks are None, they will be initialized here."""

        self.tabs = dict((n + 1, Tab(path)) for n, path in
                enumerate(self.start_paths))
        tab_list = self._get_tab_list()
        if tab_list:
            self.current_tab = tab_list[0]
            self.thistab = self.tabs[self.current_tab]
        else:
            self.current_tab = 1
            self.tabs[self.current_tab] = self.thistab = Tab('.')

        if not ranger.arg.clean and os.path.isfile(self.confpath('rifle.conf')):
            rifleconf = self.confpath('rifle.conf')
        else:
            rifleconf = self.relpath('config/rifle.conf')
        self.rifle = Rifle(rifleconf)
        self.rifle.reload_config()

        def set_image_displayer():
            self.image_displayer = self._get_image_displayer()
        set_image_displayer()
        self.settings.signal_bind('setopt.preview_images_method',
                set_image_displayer,
                priority=settings.SIGNAL_PRIORITY_AFTER_SYNC)

        if not ranger.arg.clean and self.tags is None:
            self.tags = Tags(self.confpath('tagged'))
        elif ranger.arg.clean:
            self.tags = TagsDummy("")

        if self.bookmarks is None:
            if ranger.arg.clean:
                bookmarkfile = None
            else:
                bookmarkfile = self.confpath('bookmarks')
            self.bookmarks = Bookmarks(
                    bookmarkfile=bookmarkfile,
                    bookmarktype=Directory,
                    autosave=self.settings.autosave_bookmarks)
            self.bookmarks.load()

        self.ui.setup_curses()
        self.ui.initialize()

        self.rifle.hook_before_executing = lambda a, b, flags: \
            self.ui.suspend() if 'f' not in flags else None
        self.rifle.hook_after_executing = lambda a, b, flags: \
            self.ui.initialize() if 'f' not in flags else None
        self.rifle.hook_logger = self.notify
        old_preprocessing_hook = self.rifle.hook_command_preprocessing

        # This hook allows image viewers to open all images in the current
        # directory, keeping the order of files the same as in ranger.
        # The requirements to use it are:
        # 1. set open_all_images to true
        # 2. ensure no files are marked
        # 3. call rifle with a command that starts with "sxiv " or "feh "
        def sxiv_workaround_hook(command):
            import re
            from ranger.ext.shell_escape import shell_quote

            if self.settings.open_all_images and \
                    len(self.thisdir.marked_items) == 0 and \
                    re.match(r'^(feh|sxiv|imv|pqiv) ', command):

                images = [f.relative_path for f in self.thisdir.files if f.image]
                escaped_filenames = " ".join(shell_quote(f)
                        for f in images if "\x00" not in f)

                if images and self.thisfile.relative_path in images and \
                        "$@" in command:
                    new_command = None

                    if command[0:5] == 'sxiv ':
                        number = images.index(self.thisfile.relative_path) + 1
                        new_command = command.replace("sxiv ",
                                "sxiv -n %d " % number, 1)

                    if command[0:4] == 'feh ':
                        new_command = command.replace("feh ",
                            "feh --start-at %s " %
                            shell_quote(self.thisfile.relative_path), 1)

                    if command[0:4] == 'imv ':
                        number = images.index(self.thisfile.relative_path) + 1
                        new_command = command.replace("imv ",
                                "imv -n %d " % number, 1)

                    if command[0:5] == 'pqiv ':
                        number = images.index(self.thisfile.relative_path)
                        new_command = command.replace("pqiv ",
                                "pqiv --action \"goto_file_byindex(%d)\" " %
                                number, 1)

                    if new_command:
                        command = "set -- %s; %s" % (escaped_filenames,
                                new_command)
            return old_preprocessing_hook(command)

        self.rifle.hook_command_preprocessing = sxiv_workaround_hook

        def mylogfunc(text):
            self.notify(text, bad=True)
        self.run = Runner(ui=self.ui, logfunc=mylogfunc, fm=self)

        self.settings.signal_bind('setopt.metadata_deep_search',
                lambda signal: setattr(signal.fm.metadata, 'deep_search',
                    signal.value))

    def destroy(self):
        debug = ranger.arg.debug
        if self.ui:
            try:
                self.ui.destroy()
            except Exception:
                if debug:
                    raise
        if self.loader:
            try:
                self.loader.destroy()
            except Exception:
                if debug:
                    raise

    def _get_image_displayer(self):
        if self.settings.preview_images_method == "w3m":
            return W3MImageDisplayer()
        elif self.settings.preview_images_method == "iterm2":
            return ITerm2ImageDisplayer()
        elif self.settings.preview_images_method == "urxvt":
            return URXVTImageDisplayer()
        elif self.settings.preview_images_method == "urxvt-full":
            return URXVTImageFSDisplayer()
        else:
            return ImageDisplayer()

    def _get_thisfile(self):
        return self.thistab.thisfile

    def _set_thisfile(self, obj):
        self.thistab.thisfile = obj

    def _get_thisdir(self):
        return self.thistab.thisdir

    def _set_thisdir(self, obj):
        self.thistab.thisdir = obj

    thisfile = property(_get_thisfile, _set_thisfile)
    thisdir  = property(_get_thisdir, _set_thisdir)

    def block_input(self, sec=0):
        self.input_blocked = sec != 0
        self.input_blocked_until = time() + sec

    def input_is_blocked(self):
        if self.input_blocked and time() > self.input_blocked_until:
            self.input_blocked = False
        return self.input_blocked

    def copy_config_files(self, which):
        if ranger.arg.clean:
            sys.stderr.write("refusing to copy config files in clean mode\n")
            return
        import shutil
        from errno import EEXIST

        def copy(_from, to):
            if os.path.exists(self.confpath(to)):
                sys.stderr.write("already exists: %s\n" % self.confpath(to))
            else:
                sys.stderr.write("creating: %s\n" % self.confpath(to))
                try:
                    os.makedirs(ranger.arg.confdir)
                except OSError as err:
                    if err.errno != EEXIST:  # EEXIST means it already exists
                        print("This configuration directory could not be created:")
                        print(ranger.arg.confdir)
                        print("To run ranger without the need for configuration")
                        print("files, use the --clean option.")
                        raise SystemExit()
                try:
                    shutil.copy(self.relpath(_from), self.confpath(to))
                except Exception as e:
                    sys.stderr.write("  ERROR: %s\n" % str(e))
        if which == 'rifle' or which == 'all':
            copy('config/rifle.conf', 'rifle.conf')
        if which == 'commands' or which == 'all':
            copy('config/commands_sample.py', 'commands.py')
        if which == 'commands_full' or which == 'all':
            copy('config/commands.py', 'commands_full.py')
        if which == 'rc' or which == 'all':
            copy('config/rc.conf', 'rc.conf')
        if which == 'scope' or which == 'all':
            copy('data/scope.sh', 'scope.sh')
            os.chmod(self.confpath('scope.sh'),
                os.stat(self.confpath('scope.sh')).st_mode | stat.S_IXUSR)
        if which in ('all', 'rifle', 'scope', 'commands', 'commands_full', 'rc'):
            sys.stderr.write("\n> Please note that configuration files may "
                "change as ranger evolves.\n  It's completely up to you to "
                "keep them up to date.\n")
            if os.environ.get('RANGER_LOAD_DEFAULT_RC', 0) != 'FALSE':
                sys.stderr.write("\n> To stop ranger from loading "
                "\033[1mboth\033[0m the default and your custom rc.conf,\n"
                "  please set the environment variable "
                "\033[1mRANGER_LOAD_DEFAULT_RC\033[0m to "
                "\033[1mFALSE\033[0m.\n")
        else:
            sys.stderr.write("Unknown config file `%s'\n" % which)

    def confpath(self, *paths):
        """returns the path relative to rangers configuration directory"""
        if ranger.arg.clean:
            assert 0, "Should not access relpath_conf in clean mode!"
        else:
            return os.path.join(ranger.arg.confdir, *paths)

    def relpath(self, *paths):
        """returns the path relative to rangers library directory"""
        return os.path.join(ranger.RANGERDIR, *paths)

    def get_directory(self, path):
        """Get the directory object at the given path"""
        path = os.path.abspath(path)
        try:
            return self.directories[path]
        except KeyError:
            obj = Directory(path)
            self.directories[path] = obj
            return obj

    def garbage_collect(self, age, tabs=None):  # tabs=None is for COMPATibility
        """Delete unused directory objects"""
        for key in tuple(self.directories):
            value = self.directories[key]
            if age != -1:
                if not value.is_older_than(age) \
                        or any(value in tab.pathway for tab in self.tabs.values()):
                    continue
            del self.directories[key]
            if value.is_directory:
                value.files = None
        self.settings.signal_garbage_collect()
        self.signal_garbage_collect()

    def loop(self):
        """The main loop of ranger.

        It consists of:
        1. reloading bookmarks if outdated
        2. letting the loader work
        3. drawing and finalizing ui
        4. reading and handling user input
        5. after X loops: collecting unused directory objects
        """

        self.enter_dir(self.thistab.path)

        gc_tick = 0

        # for faster lookup:
        ui = self.ui
        throbber = ui.throbber
        loader = self.loader
        has_throbber = hasattr(ui, 'throbber')
        zombies = self.run.zombies

        ranger.api.hook_ready(self)

        try:
            while True:
                loader.work()
                if has_throbber:
                    if loader.has_work():
                        throbber(loader.status)
                    else:
                        throbber(remove=True)

                ui.redraw()

                ui.set_load_mode(not loader.paused and loader.has_work())

                ui.draw_images()

                ui.handle_input()

                if zombies:
                    for zombie in tuple(zombies):
                        if zombie.poll() is not None:
                            zombies.remove(zombie)

                #gc_tick += 1
                #if gc_tick > ranger.TICKS_BEFORE_COLLECTING_GARBAGE:
                    #gc_tick = 0
                    #self.garbage_collect(ranger.TIME_BEFORE_FILE_BECOMES_GARBAGE)

        except KeyboardInterrupt:
            # this only happens in --debug mode. By default, interrupts
            # are caught in curses_interrupt_handler
            raise SystemExit

        finally:
            self.image_displayer.quit()
            if ranger.arg.choosedir and self.thisdir and self.thisdir.path:
                # XXX: UnicodeEncodeError: 'utf-8' codec can't encode character
                # '\udcf6' in position 42: surrogates not allowed
                open(ranger.arg.choosedir, 'w').write(self.thisdir.path)
            self.bookmarks.remember(self.thisdir)
            self.bookmarks.save()
