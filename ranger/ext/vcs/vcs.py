# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""VCS module"""

import os
import subprocess
import threading
import time

# Python2 compatibility
try:
    import queue
except ImportError:
    import Queue as queue
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = OSError

class VcsError(Exception):
    """VCS exception"""
    pass

class Vcs(object):
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
        'git': {'class': 'Git', 'setting': 'vcs_backend_git', 'lazy': False},
        'hg': {'class': 'Hg', 'setting': 'vcs_backend_hg', 'lazy': True},
        'bzr': {'class': 'Bzr', 'setting': 'vcs_backend_bzr', 'lazy': True},
        'svn': {'class': 'SVN', 'setting': 'vcs_backend_svn', 'lazy': True},
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
        self.is_root = True if self.obj.path == self.root else False

        self.rootvcs = None
        self.rootinit = False
        self.head = None
        self.branch = None
        self.updatetime = None
        self.track = False
        self.in_repodir = False
        self.status_subpaths = None

        if self.root:
            if self.is_root:
                self.rootvcs = self
                self.__class__ = getattr(getattr(ranger.ext.vcs, self.repotype),
                                         self.REPOTYPES[self.repotype]['class'])

                if not os.access(self.repodir, os.R_OK):
                    self.obj.vcsremotestatus = 'unknown'
                    self.obj.vcsstatus = 'unknown'
                    return

                self.track = True
            else:
                self.rootvcs = dirobj.fm.get_directory(self.root).vcs
                self.rootvcs.links |= self.links
                self.__class__ = self.rootvcs.__class__
                self.track = self.rootvcs.track

                if self.path == self.repodir or self.path.startswith(self.repodir + '/'):
                    self.in_repodir = True
                    self.track = False

    # Generic
    #---------------------------

    def _vcs(self, cmd, path, catchout=True, retbytes=False):
        """Run a VCS command"""
        with open(os.devnull, 'w') as devnull:
            try:
                if catchout:
                    output = subprocess.check_output(cmd, cwd=path, stderr=devnull)
                    return output if retbytes else output.decode('UTF-8')
                else:
                    subprocess.check_call(cmd, cwd=path, stdout=devnull, stderr=devnull)
            except (subprocess.CalledProcessError, FileNotFoundError):
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

    def init_root(self):
        """Initialize root cheaply"""
        try:
            self.head = self.data_info(self.HEAD)
            self.branch = self.data_branch()
            self.obj.vcsremotestatus = self.data_status_remote()
            self.obj.vcsstatus = self.data_status_root()
        except VcsError:
            self.update_tree(purge=True)
            return False
        self.rootinit = True
        return True

    def _update_walk(self, path, purge):
        """Update walk"""
        for wroot, wdirs, _ in os.walk(path):
            # Only update loaded directories
            try:
                wrootobj = self.obj.fm.directories[wroot]
            except KeyError:
                wdirs[:] = []
                continue
            if wrootobj.content_loaded:
                has_vcschild = False
                for fileobj in wrootobj.files_all:
                    if purge:
                        if fileobj.is_directory:
                            fileobj.vcsstatus = None
                            fileobj.vcs.__init__(fileobj)
                        else:
                            fileobj.vcsstatus = None
                        continue

                    if fileobj.is_directory:
                        fileobj.vcs.check()
                        if not fileobj.vcs.track:
                            continue
                        if fileobj.vcs.is_root:
                            has_vcschild = True
                        else:
                            fileobj.vcsstatus = self.status_subpath(
                                fileobj.path, is_directory=True)
                    else:
                        fileobj.vcsstatus = self.status_subpath(fileobj.path)
                wrootobj.has_vcschild = has_vcschild

            # Remove dead directories
            for wdir in list(wdirs):
                try:
                    wdir_obj = self.obj.fm.directories[os.path.join(wroot, wdir)]
                except KeyError:
                    wdirs.remove(wdir)
                    continue
                if wdir_obj.vcs.is_root or not wdir_obj.vcs.track:
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
            else:
                dirobj.vcsstatus = self.status_subpath(
                    os.path.realpath(dirobj.path), is_directory=True)
        if purge:
            self.__init__(self.obj)

    def update_root(self):
        """Update root state"""
        try:
            self.head = self.data_info(self.HEAD)
            self.branch = self.data_branch()
            self.status_subpaths = self.data_status_subpaths()
            self.obj.vcsremotestatus = self.data_status_remote()
            self.obj.vcsstatus = self.status_root()
        except VcsError:
            self.update_tree(purge=True)
            return False
        self.rootinit = True
        self.updatetime = time.time()
        return True

    def check(self):
        """Check health"""
        if not self.in_repodir \
                and (not self.track or (not self.is_root and self._get_repotype(self.path)[0])):
            self.__init__(self.obj)
        elif self.track and not os.path.exists(self.repodir):
            self.rootvcs.update_tree(purge=True)
            return False
        return True

    def check_outdated(self):
        """Check if root is outdated"""
        if self.updatetime is None:
            return True

        for wroot, wdirs, _ in os.walk(self.path):
            wrootobj = self.obj.fm.get_directory(wroot)
            wrootobj.load_if_outdated()
            if wroot != self.path and wrootobj.vcs.is_root:
                wdirs[:] = []
                continue

            if wrootobj.stat and self.updatetime < wrootobj.stat.st_mtime:
                return True
            if wrootobj.files_all:
                for wfile in wrootobj.files_all:
                    if wfile.stat and self.updatetime < wfile.stat.st_mtime:
                        return True
        return False

    def status_root(self):
        """Returns root status"""
        if self.status_subpaths is None:
            return 'none'

        statuses = set(status for path, status in self.status_subpaths.items())
        for status in self.DIRSTATUSES:
            if status in statuses:
                return status
        return 'sync'

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

    # Action interface
    #---------------------------

    def action_add(self, filelist):
        """Adds files to the index"""
        raise NotImplementedError

    def action_reset(self, filelist):
        """Removes files from the index"""
        raise NotImplementedError

    # Data interface
    #---------------------------

    def data_status_root(self):
        """Returns status of self.root cheaply"""
        raise NotImplementedError

    def data_status_subpaths(self):
        """Returns a dict indexed by subpaths not in sync with their status as values.
           Paths are given relative to self.root"""
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

def init_subroots(dirobj):
    """Initialize roots under dirobj"""
    redraw = False
    has_vcschild = False

    for fileobj in dirobj.files_all:
        if not fileobj.is_directory or not fileobj.vcs or not fileobj.vcs.track:
            continue
        if fileobj.vcs.is_root:
            has_vcschild = True
            if not fileobj.vcs.rootinit:
                fileobj.vcs.init_root()
        elif fileobj.is_link:
            if os.path.realpath(fileobj.path) == fileobj.vcs.root:
                has_vcschild = True
                if not fileobj.vcs.rootvcs.rootinit:
                    fileobj.vcs.rootvcs.init_root()
                fileobj.vcsstatus = fileobj.vcs.rootvcs.obj.vcsstatus
                fileobj.vcsremotestatus = fileobj.vcs.rootvcs.obj.vcsremotestatus
            else:
                fileobj.vcsstatus = fileobj.vcs.rootvcs.status_subpath(
                    os.path.realpath(fileobj.path))
            redraw = True

    if dirobj.has_vcschild != has_vcschild:
        redraw = True
        dirobj.has_vcschild = has_vcschild

    return redraw

class VcsThread(threading.Thread):
    """VCS thread"""
    def __init__(self, ui, idle_delay):
        super(VcsThread, self).__init__()
        self.daemon = True
        self.ui = ui
        self.delay = idle_delay
        self.queue = queue.Queue()
        self.wake = threading.Event()
        self.awoken = False

    def _check(self):
        """Check for hinders"""
        for column in self.ui.browser.columns:
            if column.target and column.target.is_directory and column.target.flat:
                return True
        return False

    def _targeted_directory_rightmost(self):
        """Return rightmost targeted directory"""
        target = self.ui.browser.columns[-1].target
        if target:
            if target.is_directory:
                return target
            else:
                target = self.ui.browser.columns[-2].target
                if target and target.is_directory:
                    return target
        return None

    def run(self):
        roots = set() # Handled roots
        redraw = False

        while True:
            if self._check():
                self.wake.wait(timeout=self.delay)
                if self.wake.is_set():
                    self.awoken = True
                    self.wake.clear()
                continue

            while True:
                try:
                    dirobj = self.queue.get(block=False)
                except queue.Empty:
                    break
                # Update if root
                if dirobj.vcs.track and dirobj.vcs.is_root:
                    roots.add(dirobj.vcs.path)
                    if dirobj.vcs.update_root():
                        dirobj.vcs.update_tree()
                        redraw = True
                if dirobj.files_all and init_subroots(dirobj):
                    redraw = True

            # Exclude root if repodir in the rightmost column (causes strobing)
            target = self._targeted_directory_rightmost()
            if target and target.vcs and target.vcs.in_repodir:
                roots.add(target.vcs.root)

            for column in self.ui.browser.columns:
                target = column.target
                if target and target.is_directory and target.vcs:
                    # Redraw if tree is purged
                    if not target.vcs.check():
                        redraw = True
                    if target.vcs.track and target.vcs.root not in roots:
                        roots.add(target.vcs.root)
                        lazy = target.vcs.REPOTYPES[target.vcs.repotype]['lazy']
                        if ((lazy and target.vcs.rootvcs.check_outdated()) or not lazy) \
                                and target.vcs.rootvcs.update_root():
                            target.vcs.rootvcs.update_tree()
                            redraw = True
            roots.clear()

            if redraw:
                redraw = False
                for column in self.ui.browser.columns:
                    if column.target and column.target.is_directory:
                        column.need_redraw = True
                self.ui.status.need_redraw = True
                if self.awoken:
                    self.ui.redraw()

            self.awoken = False
            self.wake.wait(timeout=self.delay)
            if self.wake.is_set():
                self.awoken = True
                self.wake.clear()

    def wakeup(self, dirobj):
        """Wakeup thread"""
        self.queue.put(dirobj)
        self.wake.set()

# Backend imports
import ranger.ext.vcs.git
import ranger.ext.vcs.hg
import ranger.ext.vcs.bzr
import ranger.ext.vcs.svn
