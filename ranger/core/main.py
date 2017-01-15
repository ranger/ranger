# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""The main function responsible to initialize the FM object and stuff."""

from __future__ import (absolute_import, print_function)

import os.path
import sys
import tempfile
from logging import getLogger

from ranger import __version__


LOG = getLogger(__name__)


def main(
        # pylint: disable=too-many-locals,too-many-return-statements
        # pylint: disable=too-many-branches,too-many-statements
):
    """initialize objects and run the filemanager"""
    import locale
    import ranger.api
    from ranger.container.settings import Settings
    from ranger.core.shared import FileManagerAware, SettingsAware
    from ranger.core.fm import FM
    from ranger.ext.logutils import setup_logging
    from ranger.ext.openstruct import OpenStruct

    ranger.args = args = parse_arguments()
    ranger.arg = OpenStruct(args.__dict__)  # COMPAT
    setup_logging(debug=args.debug, logfile=args.logfile)

    LOG.info("Ranger version %s", __version__)
    LOG.info('Running on Python ' + sys.version.replace('\n', ''))
    LOG.info("Process ID is %s", os.getpid())

    try:
        locale.setlocale(locale.LC_ALL, '')
    except Exception:
        print("Warning: Unable to set locale.  Expect encoding problems.")

    # so that programs can know that ranger spawned them:
    level = 'RANGER_LEVEL'
    if level in os.environ and os.environ[level].isdigit():
        os.environ[level] = str(int(os.environ[level]) + 1)
    else:
        os.environ[level] = '1'

    if 'SHELL' not in os.environ:
        os.environ['SHELL'] = 'sh'

    LOG.debug("config dir: '%s'", args.confdir)
    LOG.debug("cache dir: '%s'", args.cachedir)

    if args.copy_config is not None:
        fm = FM()
        fm.copy_config_files(args.copy_config)
        return 1 if args.fail_unless_cd else 0  # COMPAT
    if args.list_tagged_files:
        fm = FM()
        try:
            if sys.version_info[0] >= 3:
                fobj = open(fm.confpath('tagged'), 'r', errors='replace')
            else:
                fobj = open(fm.confpath('tagged'), 'r')
        except Exception:
            pass
        else:
            for line in fobj.readlines():
                if len(line) > 2 and line[1] == ':':
                    if line[0] in args.list_tagged_files:
                        sys.stdout.write(line[2:])
                elif line and '*' in args.list_tagged_files:
                    sys.stdout.write(line)
        return 1 if args.fail_unless_cd else 0  # COMPAT

    SettingsAware._setup(Settings())  # pylint: disable=protected-access

    if args.selectfile:
        args.selectfile = os.path.abspath(args.selectfile)
        args.targets.insert(0, os.path.dirname(args.selectfile))

    targets = args.targets or ['.']
    target = targets[0]
    if args.targets:  # COMPAT
        if target.startswith('file://'):
            target = target[7:]
        if not os.access(target, os.F_OK):
            print("File or directory doesn't exist: %s" % target)
            return 1
        elif os.path.isfile(target):
            sys.stderr.write("Warning: Using ranger as a file launcher is "
                             "deprecated.\nPlease use the standalone file launcher "
                             "'rifle' instead.\n")

            from ranger.ext.rifle import Rifle
            fm = FM()
            if not args.clean and os.path.isfile(fm.confpath('rifle.conf')):
                rifleconf = fm.confpath('rifle.conf')
            else:
                rifleconf = fm.relpath('config/rifle.conf')
            rifle = Rifle(rifleconf)
            rifle.reload_config()
            rifle.execute(targets, number=ranger.args.mode, flags=ranger.args.flags)
            return 1 if args.fail_unless_cd else 0  # COMPAT

    crash_traceback = None
    try:
        # Initialize objects
        fm = FM(paths=targets)
        FileManagerAware._setup(fm)  # pylint: disable=protected-access
        load_settings(fm, args.clean)

        if args.list_unused_keys:
            from ranger.ext.keybinding_parser import (special_keys,
                                                      reversed_special_keys)
            maps = fm.ui.keymaps['browser']
            for key in sorted(special_keys.values(), key=str):
                if key not in maps:
                    print("<%s>" % reversed_special_keys[key])
            for key in range(33, 127):
                if key not in maps:
                    print(chr(key))
            return 1 if args.fail_unless_cd else 0  # COMPAT

        if not sys.stdin.isatty():
            sys.stderr.write("Error: Must run ranger from terminal\n")
            raise SystemExit(1)

        if fm.username == 'root':
            fm.settings.preview_files = False
            fm.settings.use_preview_script = False
            LOG.info("Running as root, disabling the file previews.")
        if not args.debug:
            from ranger.ext import curses_interrupt_handler
            curses_interrupt_handler.install_interrupt_handler()

        # Create cache directory
        if fm.settings.preview_images and fm.settings.use_preview_script:
            if not os.path.exists(args.cachedir):
                os.makedirs(args.cachedir)

        # Run the file manager
        fm.initialize()
        ranger.api.hook_init(fm)
        fm.ui.initialize()

        if args.selectfile:
            fm.select_file(args.selectfile)

        if args.cmd:
            for command in args.cmd:
                fm.execute_console(command)

        if ranger.args.profile:
            import cProfile
            import pstats
            profile = None
            ranger.__fm = fm  # pylint: disable=protected-access
            cProfile.run('ranger.__fm.loop()', tempfile.gettempdir() + '/ranger_profile')
            profile = pstats.Stats(tempfile.gettempdir() + '/ranger_profile', stream=sys.stderr)
        else:
            fm.loop()
    except Exception:
        import traceback
        crash_traceback = traceback.format_exc()
    except SystemExit as error:
        return error.args[0]
    finally:
        if crash_traceback:
            try:
                filepath = fm.thisfile.path if fm.thisfile else "None"
            except Exception:
                filepath = "None"
        try:
            fm.ui.destroy()
        except (AttributeError, NameError):
            pass
        if ranger.args.profile and profile:
            profile.strip_dirs().sort_stats('cumulative').print_callees()
        if crash_traceback:
            print("ranger version: %s, executed with python %s" %
                  (ranger.__version__, sys.version.split()[0]))
            print("Locale: %s" % '.'.join(str(s) for s in locale.getlocale()))
            try:
                print("Current file: %s" % filepath)
            except Exception:
                pass
            print(crash_traceback)
            print("ranger crashed.  "
                  "Please report this traceback at:")
            print("https://github.com/hut/ranger/issues")
            return 1  # pylint: disable=lost-exception
        return 0  # pylint: disable=lost-exception


def parse_arguments():
    """Parse the program arguments"""
    from optparse import OptionParser, SUPPRESS_HELP  # pylint: disable=deprecated-module
    from os.path import expanduser
    from ranger import CONFDIR, CACHEDIR, USAGE, VERSION

    if 'XDG_CONFIG_HOME' in os.environ and os.environ['XDG_CONFIG_HOME']:
        default_confdir = os.environ['XDG_CONFIG_HOME'] + '/ranger'
    else:
        default_confdir = CONFDIR

    if 'XDG_CACHE_HOME' in os.environ and os.environ['XDG_CACHE_HOME']:
        default_cachedir = os.environ['XDG_CACHE_HOME'] + '/ranger'
    else:
        default_cachedir = CACHEDIR

    parser = OptionParser(usage=USAGE, version=VERSION)

    parser.add_option('-d', '--debug', action='store_true',
                      help="activate debug mode")
    parser.add_option('-c', '--clean', action='store_true',
                      help="don't touch/require any config files. ")
    parser.add_option('--logfile', type='string', metavar='file',
                      help="log file to use, '-' for stderr")
    parser.add_option('-r', '--confdir', type='string',
                      metavar='dir', default=default_confdir,
                      help="change the configuration directory. (%default)")
    parser.add_option('--copy-config', type='string', metavar='which',
                      help="copy the default configs to the local config directory. "
                      "Possible values: all, rc, rifle, commands, commands_full, scope")
    parser.add_option('--fail-unless-cd', action='store_true',
                      help=SUPPRESS_HELP)  # COMPAT
    parser.add_option('-m', '--mode', type='int', default=0, metavar='n',
                      help=SUPPRESS_HELP)  # COMPAT
    parser.add_option('-f', '--flags', type='string', default='',
                      metavar='string', help=SUPPRESS_HELP)  # COMPAT
    parser.add_option('--choosefile', type='string', metavar='TARGET',
                      help="Makes ranger act like a file chooser. When opening "
                      "a file, it will quit and write the name of the selected "
                      "file to TARGET.")
    parser.add_option('--choosefiles', type='string', metavar='TARGET',
                      help="Makes ranger act like a file chooser for multiple files "
                      "at once. When opening a file, it will quit and write the name "
                      "of all selected files to TARGET.")
    parser.add_option('--choosedir', type='string', metavar='TARGET',
                      help="Makes ranger act like a directory chooser. When ranger quits"
                      ", it will write the name of the last visited directory to TARGET")
    parser.add_option('--selectfile', type='string', metavar='filepath',
                      help="Open ranger with supplied file selected.")
    parser.add_option('--list-unused-keys', action='store_true',
                      help="List common keys which are not bound to any action.")
    parser.add_option('--list-tagged-files', type='string', default=None,
                      metavar='tag',
                      help="List all files which are tagged with the given tag, default: *")
    parser.add_option('--profile', action='store_true',
                      help="Print statistics of CPU usage on exit.")
    parser.add_option('--cmd', action='append', type='string', metavar='COMMAND',
                      help="Execute COMMAND after the configuration has been read. "
                      "Use this option multiple times to run multiple commands.")

    args, positional = parser.parse_args()
    args.targets = positional
    args.confdir = expanduser(args.confdir)
    args.cachedir = expanduser(default_cachedir)

    if args.fail_unless_cd:  # COMPAT
        sys.stderr.write("Warning: The option --fail-unless-cd is deprecated.\n"
                         "It was used to facilitate using ranger as a file launcher.\n"
                         "Now, please use the standalone file launcher 'rifle' instead.\n")

    return args


COMMANDS_EXCLUDE = ['settings', 'notify']


def load_settings(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        fm, clean):
    from ranger.core.actions import Actions
    import ranger.core.shared
    import ranger.api.commands
    from ranger.config import commands as commands_default

    # Load default commands
    fm.commands = ranger.api.commands.CommandContainer()
    include = [name for name in dir(Actions) if name not in COMMANDS_EXCLUDE]
    fm.commands.load_commands_from_object(fm, include)
    fm.commands.load_commands_from_module(commands_default)

    if not clean:
        allow_access_to_confdir(ranger.args.confdir, True)

        # Load custom commands
        custom_comm_path = fm.confpath('commands.py')
        if os.path.exists(custom_comm_path):
            old_bytecode_setting = sys.dont_write_bytecode
            sys.dont_write_bytecode = True
            try:
                import commands as commands_custom
                fm.commands.load_commands_from_module(commands_custom)
            except ImportError as ex:
                LOG.debug("Failed to import custom commands from '%s'", custom_comm_path)
                LOG.exception(ex)
            else:
                LOG.debug("Loaded custom commands from '%s'", custom_comm_path)
            sys.dont_write_bytecode = old_bytecode_setting

        allow_access_to_confdir(ranger.args.confdir, False)

        # Load rc.conf
        custom_conf = fm.confpath('rc.conf')
        default_conf = fm.relpath('config', 'rc.conf')

        if os.environ.get('RANGER_LOAD_DEFAULT_RC', 0) != 'FALSE':
            fm.source(default_conf)
        if os.access(custom_conf, os.R_OK):
            fm.source(custom_conf)

        allow_access_to_confdir(ranger.args.confdir, True)

        # XXX Load plugins (experimental)
        try:
            plugindir = fm.confpath('plugins')
            plugins = [p[:-3] for p in os.listdir(plugindir)
                       if p.endswith('.py') and not p.startswith('_')]
        except Exception:
            pass
        else:
            if not os.path.exists(fm.confpath('plugins', '__init__.py')):
                LOG.debug("Creating missing '__init__.py' file in plugin folder")
                fobj = open(fm.confpath('plugins', '__init__.py'), 'w')
                fobj.close()

            ranger.fm = fm
            for plugin in sorted(plugins):
                try:
                    try:
                        # importlib does not exist before python2.7.  It's
                        # required for loading commands from plugins, so you
                        # can't use that feature in python2.6.
                        import importlib
                    except ImportError:
                        module = __import__('plugins', fromlist=[plugin])
                    else:
                        module = importlib.import_module('plugins.' + plugin)
                        fm.commands.load_commands_from_module(module)
                    LOG.debug("Loaded plugin '%s'", plugin)
                except Exception as ex:
                    ex_msg = "Error while loading plugin '{0}'".format(plugin)
                    LOG.error(ex_msg)
                    LOG.exception(ex)
                    fm.notify(ex_msg, bad=True)
            ranger.fm = None

        # COMPAT: Load the outdated options.py
        # options.py[oc] are deliberately ignored
        if os.path.exists(fm.confpath("options.py")):
            module = __import__('options')
            from ranger.container.settings import ALLOWED_SETTINGS
            for setting in ALLOWED_SETTINGS:
                if hasattr(module, setting):
                    fm.settings[setting] = getattr(module, setting)

            sys.stderr.write(
                """******************************
Warning: The configuration file 'options.py' is deprecated.
Please move all settings to the file 'rc.conf', converting lines like
    "preview_files = False"
to
    "set preview_files false"
If you had python code in the options.py that you'd like to keep, simply
copy & paste it to a .py file in ~/.config/ranger/plugins/.
Remove the options.py or discard stderr to get rid of this warning.
******************************\n""")

        allow_access_to_confdir(ranger.args.confdir, False)
    else:
        fm.source(fm.relpath('config', 'rc.conf'))


def allow_access_to_confdir(confdir, allow):
    from errno import EEXIST

    if allow:
        try:
            os.makedirs(confdir)
        except OSError as err:
            if err.errno != EEXIST:  # EEXIST means it already exists
                print("This configuration directory could not be created:")
                print(confdir)
                print("To run ranger without the need for configuration")
                print("files, use the --clean option.")
                raise SystemExit()
        else:
            LOG.debug("Created config directory '%s'", confdir)
        if confdir not in sys.path:
            sys.path[0:0] = [confdir]
    else:
        if sys.path[0] == confdir:
            del sys.path[0]
