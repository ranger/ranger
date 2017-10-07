# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""The main function responsible to initialize the FM object and stuff."""

from __future__ import (absolute_import, division, print_function)

from logging import getLogger
import locale
import os.path
import sys
import tempfile

from ranger import VERSION


LOG = getLogger(__name__)

VERSION_MSG = [
    'ranger version: {0}'.format(VERSION),
    'Python version: {0}'.format(' '.join(line.strip() for line in sys.version.splitlines())),
    'Locale: {0}'.format('.'.join(str(s) for s in locale.getlocale())),
]


def main(
        # pylint: disable=too-many-locals,too-many-return-statements
        # pylint: disable=too-many-branches,too-many-statements
):
    """initialize objects and run the filemanager"""
    import ranger.api
    from ranger.container.settings import Settings
    from ranger.core.shared import FileManagerAware, SettingsAware
    from ranger.core.fm import FM
    from ranger.ext.logutils import setup_logging
    from ranger.ext.openstruct import OpenStruct

    ranger.args = args = parse_arguments()
    ranger.arg = OpenStruct(args.__dict__)  # COMPAT
    setup_logging(debug=args.debug, logfile=args.logfile)

    for line in VERSION_MSG:
        LOG.info(line)
    LOG.info('Process ID: %s', os.getpid())

    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        print("Warning: Unable to set locale.  Expect encoding problems.")

    # so that programs can know that ranger spawned them:
    level = 'RANGER_LEVEL'
    if level in os.environ and os.environ[level].isdigit():
        os.environ[level] = str(int(os.environ[level]) + 1)
    else:
        os.environ[level] = '1'

    if 'SHELL' not in os.environ:
        os.environ['SHELL'] = 'sh'

    LOG.debug("cache dir: '%s'", args.cachedir)
    LOG.debug("config dir: '%s'", args.confdir)
    LOG.debug("data dir: '%s'", args.datadir)

    if args.copy_config is not None:
        fm = FM()
        fm.copy_config_files(args.copy_config)
        return 0
    if args.list_tagged_files:
        if args.clean:
            print("Can't access tag data in clean mode", file=sys.stderr)
            return 1
        fm = FM()
        try:
            if sys.version_info[0] >= 3:
                fobj = open(fm.datapath('tagged'), 'r', errors='replace')
            else:
                fobj = open(fm.datapath('tagged'), 'r')
        except OSError as ex:
            print('Unable to open `tagged` data file: {0}'.format(ex), file=sys.stderr)
            return 1
        for line in fobj.readlines():
            if len(line) > 2 and line[1] == ':':
                if line[0] in args.list_tagged_files:
                    sys.stdout.write(line[2:])
            elif line and '*' in args.list_tagged_files:
                sys.stdout.write(line)
        return 0

    SettingsAware.settings_set(Settings())

    if args.selectfile:
        args.selectfile = os.path.abspath(args.selectfile)
        args.paths.insert(0, os.path.dirname(args.selectfile))

    if args.paths:
        paths = [p[7:] if p.startswith('file:///') else p for p in args.paths]
    else:
        paths = [os.environ.get('PWD', os.getcwd())]
    paths_inaccessible = []
    for path in paths:
        try:
            path_abs = os.path.abspath(path)
        except OSError:
            paths_inaccessible += [path]
            continue
        if not os.access(path_abs, os.F_OK):
            paths_inaccessible += [path]
    if paths_inaccessible:
        print('Inaccessible paths: {0}'.format(paths), file=sys.stderr)
        return 1

    profile = None
    exit_msg = ''
    exit_code = 0
    try:  # pylint: disable=too-many-nested-blocks
        # Initialize objects
        fm = FM(paths=paths)
        FileManagerAware.fm_set(fm)
        load_settings(fm, args.clean)

        if args.show_only_dirs:
            from ranger.container.directory import InodeFilterConstants
            fm.settings.global_inode_type_filter = InodeFilterConstants.DIRS

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
            return 0

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

        if not args.clean:
            # Create data directory
            if not os.path.exists(args.datadir):
                os.makedirs(args.datadir)

            # Restore saved tabs
            tabs_datapath = fm.datapath('tabs')
            if fm.settings.save_tabs_on_exit and os.path.exists(tabs_datapath) and not args.paths:
                try:
                    with open(tabs_datapath, 'r') as fobj:
                        tabs_saved = fobj.read().partition('\0\0')
                        fm.start_paths += tabs_saved[0].split('\0')
                    if tabs_saved[-1]:
                        with open(tabs_datapath, 'w') as fobj:
                            fobj.write(tabs_saved[-1])
                    else:
                        os.remove(tabs_datapath)
                except OSError as ex:
                    LOG.error('Unable to restore saved tabs')
                    LOG.exception(ex)

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
            ranger.__fm = fm  # pylint: disable=protected-access
            profile_file = tempfile.gettempdir() + '/ranger_profile'
            cProfile.run('ranger.__fm.loop()', profile_file)
            profile = pstats.Stats(profile_file, stream=sys.stderr)
        else:
            fm.loop()

    except Exception:  # pylint: disable=broad-except
        import traceback
        ex_traceback = traceback.format_exc()
        exit_msg += '\n'.join(VERSION_MSG) + '\n'
        try:
            exit_msg += "Current file: {0}\n".format(repr(fm.thisfile.path))
        except Exception:  # pylint: disable=broad-except
            pass
        exit_msg += '''
{0}
ranger crashed. Please report this traceback at:
https://github.com/ranger/ranger/issues
'''.format(ex_traceback)

        exit_code = 1

    except SystemExit as ex:
        if ex.code is not None:
            if not isinstance(ex.code, int):
                exit_msg = ex.code
                exit_code = 1
            else:
                exit_code = ex.code

    finally:
        if exit_msg:
            LOG.critical(exit_msg)
        try:
            fm.ui.destroy()
        except (AttributeError, NameError):
            pass
        # If profiler is enabled print the stats
        if ranger.args.profile and profile:
            profile.strip_dirs().sort_stats('cumulative').print_callees()
        # print the exit message if any
        if exit_msg:
            sys.stderr.write(exit_msg)
        return exit_code  # pylint: disable=lost-exception


def xdg_path(env_var):
    path = os.environ.get(env_var)
    if path and os.path.isabs(path):
        return os.path.join(path, 'ranger')
    return None


def parse_arguments():
    """Parse the program arguments"""
    from optparse import OptionParser  # pylint: disable=deprecated-module
    from ranger import CONFDIR, CACHEDIR, DATADIR, USAGE

    parser = OptionParser(usage=USAGE, version=('\n'.join(VERSION_MSG)))

    parser.add_option('-d', '--debug', action='store_true',
                      help="activate debug mode")
    parser.add_option('-c', '--clean', action='store_true',
                      help="don't touch/require any config files. ")
    parser.add_option('--logfile', type='string', metavar='file',
                      help="log file to use, '-' for stderr")
    parser.add_option('--cachedir', type='string',
                      metavar='dir', default=(xdg_path('XDG_CACHE_HOME') or CACHEDIR),
                      help="change the cache directory. (%default)")
    parser.add_option('-r', '--confdir', type='string',
                      metavar='dir', default=(xdg_path('XDG_CONFIG_HOME') or CONFDIR),
                      help="change the configuration directory. (%default)")
    parser.add_option('--datadir', type='string',
                      metavar='dir', default=(xdg_path('XDG_DATA_HOME') or DATADIR),
                      help="change the data directory. (%default)")
    parser.add_option('--copy-config', type='string', metavar='which',
                      help="copy the default configs to the local config directory. "
                      "Possible values: all, rc, rifle, commands, commands_full, scope")
    parser.add_option('--choosefile', type='string', metavar='PATH',
                      help="Makes ranger act like a file chooser. When opening "
                      "a file, it will quit and write the name of the selected "
                      "file to PATH.")
    parser.add_option('--choosefiles', type='string', metavar='PATH',
                      help="Makes ranger act like a file chooser for multiple files "
                      "at once. When opening a file, it will quit and write the name "
                      "of all selected files to PATH.")
    parser.add_option('--choosedir', type='string', metavar='PATH',
                      help="Makes ranger act like a directory chooser. When ranger quits"
                      ", it will write the name of the last visited directory to PATH")
    parser.add_option('--show-only-dirs', action='store_true',
                      help="Show only directories, no files or links")
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
    args.paths = positional

    def path_init(option):
        argval = args.__dict__[option]
        try:
            path = os.path.realpath(argval)
        except OSError as ex:
            sys.stderr.write(
                '--{0} is not accessible: {1}\n{2}\n'.format(option, argval, str(ex)))
            sys.exit(1)
        if os.path.exists(path) and not os.access(path, os.W_OK):
            sys.stderr.write('--{0} is not writable: {1}\n'.format(option, path))
            sys.exit(1)
        return path

    args.cachedir = path_init('cachedir')
    args.confdir = path_init('confdir')
    args.datadir = path_init('datadir')
    if args.choosefile:
        args.choosefile = path_init('choosefile')
    if args.choosefiles:
        args.choosefiles = path_init('choosefiles')
    if args.choosedir:
        args.choosedir = path_init('choosedir')

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

        # XXX Load plugins (experimental)
        plugindir = fm.confpath('plugins')
        try:
            plugin_files = os.listdir(plugindir)
        except OSError:
            LOG.debug('Unable to access plugin directory: %s', plugindir)
        else:
            plugins = [p[:-3] for p in plugin_files
                       if p.endswith('.py') and not p.startswith('_')]
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
                except Exception as ex:  # pylint: disable=broad-except
                    ex_msg = "Error while loading plugin '{0}'".format(plugin)
                    LOG.error(ex_msg)
                    LOG.exception(ex)
                    fm.notify(ex_msg, bad=True)
            ranger.fm = None

        allow_access_to_confdir(ranger.args.confdir, False)
        # Load rc.conf
        custom_conf = fm.confpath('rc.conf')
        default_conf = fm.relpath('config', 'rc.conf')

        custom_conf_is_readable = os.access(custom_conf, os.R_OK)
        if (os.environ.get('RANGER_LOAD_DEFAULT_RC', 'TRUE').upper() != 'FALSE' or
                not custom_conf_is_readable):
            fm.source(default_conf)
        if custom_conf_is_readable:
            fm.source(custom_conf)

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
                raise SystemExit
        else:
            LOG.debug("Created config directory '%s'", confdir)
        if confdir not in sys.path:
            sys.path[0:0] = [confdir]
    else:
        if sys.path[0] == confdir:
            del sys.path[0]
