# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""VCS module"""

from __future__ import (absolute_import, division, print_function)

import os
import subprocess
import threading
import time

from ranger.ext import spawn

# Python 2 compatibility
try:
    import queue
except ImportError:
    import Queue as queue  # pylint: disable=import-error


class VcsError(Exception):
    """VCS exception"""


class Vcs(object):  # pylint: disable=too-many-instance-attributes
    """
    This class represents a version controlled path, abstracting the usual
    operations from the different supported backends.

    The backends are declared in REPOTYPES, and are derived
    classes from Vcs with the following restrictions:

     * Override ALL interface methods
     * Only override interface methods
     * Do NOT modify internal state. All internal state is handled by Vcs

    """

    # These are abstracted revisions, representing the current index (staged files),
    # the current head and nothing. Every backend should redefine them if the
    # version control has a similar concept, or implement _sanitize_rev method to
    # clean the rev before using them
    INDEX = 'INDEX'
    HEAD = 'HEAD'
    NONE = 'NONE'

    # Backends
    REPOTYPES = {
        'bzr': {'class': 'Bzr', 'setting': 'vcs_backend_bzr'},
        'git': {'class': 'Git', 'setting': 'vcs_backend_git'},
        'hg': {'class': 'Hg', 'setting': 'vcs_backend_hg'},
        'svn': {'class': 'SVN', 'setting': 'vcs_backend_svn'},
    }

    # Possible directory statuses in order of importance
    # statuses that should not be inherited from subpaths are disabled
    DIRSTATUSES = (
        'conflict',
        'untracked',
        'deleted',
        'changed',
        'staged',
        # 'ignored',
        'sync',
        # 'none',
        'unknown',
    )

    def __init__(self, dirobj):
        self.obj = dirobj
        self.path = dirobj.path
        self.repotypes_settings = set(
            repotype for repotype, values in self.REPOTYPES.items()
            if getattr(dirobj.settings, values['setting']) in ('enabled', 'local')
        )

        self.root, self.repodir, self.repotype, self.links = self._find_root(self.path)
        self.is_root = self.obj.path == self.root
        self.is_root_link = (
            self.obj.is_link and self.obj.realpath == self.root)
        self.is_root_pointer = self.is_root or self.is_root_link
        self.in_repodir = False
        self.rootvcs = None
        self.track = False

        if self.root:
            if self.is_root:
                self.rootvcs = self
                self.__class__ = globals()[self.REPOTYPES[self.repotype]['class'] + 'Root']

                if not os.access(self.repodir, os.R_OK):
                    self.obj.vcsremotestatus = 'unknown'
                    self.obj.vcsstatus = 'unknown'
                    return

                self.track = True
            else:
                self.rootvcs = dirobj.fm.get_directory(self.root).vcs
                if self.rootvcs is None or self.rootvcs.root is None:
                    return
                self.rootvcs.links |= self.links
                self.__class__ = globals()[self.REPOTYPES[self.repotype]['class']]
                self.track = self.rootvcs.track

                if self.path == self.repodir or self.path.startswith(self.repodir + '/'):
                    self.in_repodir = True
                    self.track = False

    # Generic

    def _run(self, args, path=None,  # pylint: disable=too-many-arguments
             catchout=True, retbytes=False, rstrip_newline=True):
        """Run a command"""
        if self.repotype == 'hg':
            # use "chg", a faster built-in client
            cmd = ['chg'] + args
        else:
            cmd = [self.repotype] + args
        if path is None:
            path = self.path

        try:
            if catchout:
                output = spawn.check_output(cmd, cwd=path, decode=not retbytes)
                if not retbytes and rstrip_newline and output.endswith('\n'):
                    return output[:-1]
                return output
            else:
                with open(os.devnull, mode='w') as fd_devnull:
                    subprocess.check_call(cmd, cwd=path, stdout=fd_devnull, stderr=fd_devnull)
                return None
        except (subprocess.CalledProcessError, OSError):
            raise VcsError('{0:s}: {1:s}'.format(str(cmd), path))

    def _get_repotype(self, path):
        """Get type for path"""
        for repotype in self.repotypes_settings:
            repodir = os.path.join(path, '.' + repotype)
            if os.path.exists(repodir):
                return (repodir, repotype)
        return (None, None)

    def _find_root(self, path):
        """Finds root path"""
        links = set()
        while True:
            if os.path.islink(path):
                links.add(path)
                relpath = os.path.relpath(self.path, path)
                path = os.path.realpath(path)
                self.path = os.path.normpath(os.path.join(path, relpath))

            repodir, repotype = self._get_repotype(path)
            if repodir:
                return (path, repodir, repotype, links)

            path_old = path
            path = os.path.dirname(path)
            if path == path_old:
                break

        return (None, None, None, None)

    def reinit(self):
        """Reinit"""
        if not self.in_repodir:
            if not self.track \
                    or (not self.is_root_pointer and self._get_repotype(self.obj.realpath)[0]) \
                    or not os.path.exists(self.repodir):
                self.__init__(self.obj)

    # Action interface

    def action_add(self, filelist):
        """Adds files to the index"""
        raise NotImplementedError

    def action_reset(self, filelist):
        """Removes files from the index"""
        raise NotImplementedError

    # Data interface

    def data_status_root(self):
        """Returns status of self.root cheaply"""
        raise NotImplementedError

    def data_status_subpaths(self):
        """
        Returns a dict indexed by subpaths not in sync with their status as values.
        Paths are given relative to self.root
        """
        raise NotImplementedError

    def data_status_remote(self):
        """
        Returns remote status of repository
        One of ('sync', 'ahead', 'behind', 'diverged', 'none')
        """
        raise NotImplementedError

    def data_branch(self):
        """Returns the current named branch, if this makes sense for the backend. None otherwise"""
        raise NotImplementedError

    def data_info(self, rev=None):
        """Returns info string about revision rev. None in special cases"""
        raise NotImplementedError


class VcsRoot(Vcs):  # pylint: disable=abstract-method
    """Vcs root"""
    rootinit = False
    head = None
    branch = None
    updatetime = None
    status_subpaths = None

    def _status_root(self):
        """Returns root status"""
        if self.status_subpaths is None:
            return 'none'

        statuses = set(status for path, status in self.status_subpaths.items())
        for status in self.DIRSTATUSES:
            if status in statuses:
                return status
        return 'sync'

    def init_root(self):
        """Initialize root cheaply"""
        try:
            self.head = self.data_info(self.HEAD)
            self.branch = self.data_branch()
            self.obj.vcsremotestatus = self.data_status_remote()
            self.obj.vcsstatus = self.data_status_root()
        except VcsError as ex:
            self.obj.fm.notify('VCS Exception: View log for more info', bad=True, exception=ex)
            return False
        self.rootinit = True
        return True

    def update_root(self):
        """Update root state"""
        try:
            self.head = self.data_info(self.HEAD)
            self.branch = self.data_branch()
            self.status_subpaths = self.data_status_subpaths()
            self.obj.vcsremotestatus = self.data_status_remote()
            self.obj.vcsstatus = self._status_root()
        except VcsError as ex:
            self.obj.fm.notify('VCS Exception: View log for more info', bad=True, exception=ex)
            return False
        self.rootinit = True
        self.updatetime = time.time()
        return True

    def _update_walk(self, path, purge):  # pylint: disable=too-many-branches
        """Update walk"""
        for wroot, wdirs, _ in os.walk(path):
            # Only update loaded directories
            try:
                wrootobj = self.obj.fm.directories[wroot]
            except KeyError:
                wdirs[:] = []
                continue
            if not wrootobj.vcs.track:
                wdirs[:] = []
                continue

            if wrootobj.content_loaded:
                has_vcschild = False
                for fsobj in wrootobj.files_all:
                    if purge:
                        if fsobj.is_directory:
                            fsobj.vcsstatus = None
                            fsobj.vcs.__init__(fsobj)
                        else:
                            fsobj.vcsstatus = None
                        continue

                    if fsobj.is_directory:
                        fsobj.vcs.reinit()
                        if not fsobj.vcs.track:
                            continue
                        if fsobj.vcs.is_root_pointer:
                            has_vcschild = True
                        else:
                            fsobj.vcsstatus = self.status_subpath(
                                os.path.join(wrootobj.realpath, fsobj.basename),
                                is_directory=True,
                            )
                    else:
                        fsobj.vcsstatus = self.status_subpath(
                            os.path.join(wrootobj.realpath, fsobj.basename))
                wrootobj.has_vcschild = has_vcschild

            # Remove dead directories
            for wdir in list(wdirs):
                try:
                    wdirobj = self.obj.fm.directories[os.path.join(wroot, wdir)]
                except KeyError:
                    wdirs.remove(wdir)
                    continue
                if not wdirobj.vcs.track or wdirobj.vcs.is_root_pointer:
                    wdirs.remove(wdir)

    def update_tree(self, purge=False):
        """Update tree state"""
        self._update_walk(self.path, purge)
        for path in list(self.links):
            self._update_walk(path, purge)
            try:
                dirobj = self.obj.fm.directories[path]
            except KeyError:
                self.links.remove(path)
                continue
            if purge:
                dirobj.vcsstatus = None
                dirobj.vcs.__init__(dirobj)
            elif dirobj.vcs.path == self.path:
                dirobj.vcsremotestatus = self.obj.vcsremotestatus
                dirobj.vcsstatus = self.obj.vcsstatus
        if purge:
            self.__init__(self.obj)

    def check_outdated(self):
        """Check if root is outdated"""
        if self.updatetime is None:
            return True

        for wroot, wdirs, _ in os.walk(self.path):
            wrootobj = self.obj.fm.get_directory(wroot)
            wrootobj.load_if_outdated()
            if wroot != self.path and wrootobj.vcs.is_root_pointer:
                wdirs[:] = []
                continue

            if wrootobj.stat and self.updatetime < wrootobj.stat.st_mtime:
                return True
            if wrootobj.files_all:
                for wfile in wrootobj.files_all:
                    if wfile.stat and self.updatetime < wfile.stat.st_mtime:
                        return True
        return False

    def status_subpath(self, path, is_directory=False):
        """
        Returns the status of path

        path needs to be self.obj.path or subpath thereof
        """
        if self.status_subpaths is None:
            return 'none'

        relpath = os.path.relpath(path, self.path)

        # check if relpath or its parents has a status
        tmppath = relpath
        while tmppath:
            if tmppath in self.status_subpaths:
                return self.status_subpaths[tmppath]
            tmppath = os.path.dirname(tmppath)

        # check if path contains some file in status
        if is_directory:
            statuses = set(status for subpath, status in self.status_subpaths.items()
                           if subpath.startswith(relpath + '/'))
            for status in self.DIRSTATUSES:
                if status in statuses:
                    return status
        return 'sync'


class VcsThread(threading.Thread):  # pylint: disable=too-many-instance-attributes
    """VCS thread"""

    def __init__(self, ui):
        super(VcsThread, self).__init__()
        self.daemon = True
        self._ui = ui
        self._queue = queue.Queue()
        self.__stop = threading.Event()
        self.stopped = threading.Event()
        self._advance = threading.Event()
        self._advance.set()
        self.paused = threading.Event()
        self._awoken = threading.Event()
        self._redraw = False
        self._roots = set()

    def _is_targeted(self, dirobj):
        """Check if dirobj is targeted"""
        if self._ui.browser.main_column and self._ui.browser.main_column.target == dirobj:
            return True
        return False

    def _update_subroots(self, fsobjs):
        """Update subroots"""
        if not fsobjs:
            return False

        has_vcschild = False
        for fsobj in fsobjs:
            if not fsobj.is_directory or not fsobj.vcs or not fsobj.vcs.track:
                continue

            rootvcs = fsobj.vcs.rootvcs
            if fsobj.vcs.is_root_pointer:
                has_vcschild = True
                if not rootvcs.rootinit and not self._is_targeted(rootvcs.obj):
                    self._roots.add(rootvcs.path)
                    if not rootvcs.init_root():
                        rootvcs.update_tree(purge=True)
                    self._redraw = True
                if fsobj.is_link:
                    fsobj.vcsstatus = rootvcs.obj.vcsstatus
                    fsobj.vcsremotestatus = rootvcs.obj.vcsremotestatus
                    self._redraw = True

        return has_vcschild

    def _queue_process(self):  # pylint: disable=too-many-branches
        """Process queue"""
        dirobjs = []
        paths = set()
        self._roots.clear()

        while True:
            try:
                dirobjs.append(self._queue.get(block=False))
            except queue.Empty:
                break

        for dirobj in dirobjs:
            if dirobj.path in paths:
                continue
            paths.add(dirobj.path)

            dirobj.vcs.reinit()
            if dirobj.vcs.track:
                rootvcs = dirobj.vcs.rootvcs
                if rootvcs.path not in self._roots and rootvcs.check_outdated():
                    self._roots.add(rootvcs.path)
                    if rootvcs.update_root():
                        rootvcs.update_tree()
                    else:
                        rootvcs.update_tree(purge=True)
                    self._redraw = True

            has_vcschild = self._update_subroots(dirobj.files_all)

            if dirobj.has_vcschild != has_vcschild:
                dirobj.has_vcschild = has_vcschild
                self._redraw = True

    def run(self):
        while True:
            self.paused.set()
            self._advance.wait()
            self._awoken.wait()
            if self.__stop.isSet():
                self.stopped.set()
                return
            if not self._advance.isSet():
                continue
            self._awoken.clear()
            self.paused.clear()

            try:
                self._queue_process()

                if self._redraw:
                    self._redraw = False
                    for column in self._ui.browser.columns:
                        if column.target and column.target.is_directory:
                            column.need_redraw = True
                    self._ui.status.need_redraw = True
                    self._ui.redraw()
            except Exception as ex:  # pylint: disable=broad-except
                self._ui.fm.notify('VCS Exception: View log for more info', bad=True, exception=ex)

    def stop(self):
        """Stop thread synchronously"""
        self.__stop.set()
        self.paused.wait(5)
        self._advance.set()
        self._awoken.set()
        self.stopped.wait(1)
        return self.stopped.isSet()

    def pause(self):
        """Pause thread"""
        self._advance.clear()

    def unpause(self):
        """Unpause thread"""
        self._advance.set()

    def process(self, dirobj):
        """Process dirobj"""
        self._queue.put(dirobj)
        self._awoken.set()


# Backend imports
from .bzr import Bzr  # NOQA pylint: disable=wrong-import-position
from .git import Git  # NOQA pylint: disable=wrong-import-position
from .hg import Hg  # NOQA pylint: disable=wrong-import-position
from .svn import SVN  # NOQA pylint: disable=wrong-import-position


class BzrRoot(VcsRoot, Bzr):
    """Bzr root"""


class GitRoot(VcsRoot, Git):
    """Git root"""


class HgRoot(VcsRoot, Hg):
    """Hg root"""


class SVNRoot(VcsRoot, SVN):
    """SVN root"""
