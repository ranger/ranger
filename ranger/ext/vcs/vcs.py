# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""VCS module"""

import os
import subprocess
import threading

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
        'git': {'class': 'Git', 'setting': 'vcs_backend_git'},
        'hg': {'class': 'Hg', 'setting': 'vcs_backend_hg'},
        'bzr': {'class': 'Bzr', 'setting': 'vcs_backend_bzr'},
        'svn': {'class': 'SVN', 'setting': 'vcs_backend_svn'},
    }

    # Possible directory statuses in order of importance with statuses that
    # don't make sense disabled
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

    def __init__(self, directoryobject):
        self.obj = directoryobject
        self.path = self.obj.path
        self.repotypes_settings = set(
            repotype for repotype, values in self.REPOTYPES.items()
            if getattr(self.obj.settings, values['setting']) in ('enabled', 'local')
        )
        self.in_repodir = False
        self.track = False

        self.root, self.repodir, self.repotype, self.links = self._find_root(self.path)
        self.is_root = True if self.obj.path == self.root else False

        if self.root:
            if self.is_root:
                self.rootvcs = self
                self.__class__ = getattr(getattr(ranger.ext.vcs, self.repotype),
                                         self.REPOTYPES[self.repotype]['class'])
                self.status_subpaths = {}

                if not os.access(self.repodir, os.R_OK):
                    directoryobject.vcsstatus = 'unknown'
                    self.remotestatus = 'unknown'
                    return

                try:
                    self.head = self.data_info(self.HEAD)
                    self.branch = self.data_branch()
                    self.remotestatus = self.data_status_remote()
                    self.obj.vcsstatus = self.data_status_root()
                except VcsError:
                    return

                self.track = True
            else:
                self.rootvcs = directoryobject.fm.get_directory(self.root).vcs
                self.rootvcs.links |= self.links
                self.__class__ = self.rootvcs.__class__

                # Do not track self.repodir or its subpaths
                if self.path == self.repodir or self.path.startswith(self.repodir + '/'):
                    self.in_repodir = True
                    return

                self.track = self.rootvcs.track

    # Generic
    #---------------------------

    def _vcs(self, path, cmd, args, silent=False, catchout=False, retbytes=False):
        """Run a VCS command"""
        with open(os.devnull, 'w') as devnull:
            out = devnull if silent else None
            try:
                if catchout:
                    output = subprocess.check_output([cmd] + args, stderr=out, cwd=path)
                    return output if retbytes else output.decode('UTF-8').strip()
                else:
                    subprocess.check_call([cmd] + args, stderr=out, stdout=out, cwd=path)
            except subprocess.CalledProcessError:
                raise VcsError("{0:s} error on {1:s}. Command: {2:s}"\
                               .format(cmd, path, ' '.join([cmd] + args)))
            except FileNotFoundError:
                raise VcsError("{0:s} error on {1:s}: File not found".format(cmd, path))

    def _get_repotype(self, path):
        """Get type for path"""
        for repotype in self.repotypes_settings:
            repodir = os.path.join(path, '.{0:s}'.format(repotype))
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

    def _update_walk(self, path, purge):
        """Update walk"""
        for wroot, wdirs, _ in os.walk(path):
            # Only update loaded directories
            try:
                wroot_obj = self.obj.fm.directories[wroot]
            except KeyError:
                wdirs[:] = []
                continue
            if wroot_obj.content_loaded:
                for fileobj in wroot_obj.files_all:
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
                        if not fileobj.vcs.is_root:
                            fileobj.vcsstatus = wroot_obj.vcs.status_subpath(
                                fileobj.path, is_directory=True)
                    else:
                        fileobj.vcsstatus = wroot_obj.vcs.status_subpath(fileobj.path)

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
        self._update_walk(self.root, purge)
        for path in list(self.rootvcs.links):
            self._update_walk(path, purge)
            try:
                dirobj = self.obj.fm.directories[path]
            except KeyError:
                continue
            if purge:
                dirobj.vcsstatus = None
                dirobj.vcs.__init__(dirobj.vcs.obj)
            elif dirobj.vcs.path == self.root:
                dirobj.vcsstatus = self.rootvcs.status_root()
            else:
                dirobj.vcsstatus = dirobj.vcs.status_subpath(dirobj.path, is_directory=True)
        if purge:
            self.rootvcs.__init__(self.rootvcs.obj)

    def update_root(self):
        """Update root state"""
        try:
            self.rootvcs.head = self.rootvcs.data_info(self.HEAD)
            self.rootvcs.branch = self.rootvcs.data_branch()
            self.rootvcs.status_subpaths = self.rootvcs.data_status_subpaths()
            self.rootvcs.remotestatus = self.rootvcs.data_status_remote()
            self.rootvcs.obj.vcsstatus = self.rootvcs.status_root()
        except VcsError:
            self.update_tree(purge=True)
            return False
        return True

    def check(self):
        """Check health"""
        if not self.in_repodir \
                and (not self.track or (not self.is_root and self._get_repotype(self.path)[0])):
            self.__init__(self.obj)
        elif self.track and not os.path.exists(self.repodir):
            self.update_tree(purge=True)
            return False
        return True

    def status_root(self):
        """Returns root status"""
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
        if path == self.obj.path:
            relpath = os.path.relpath(self.path, self.root)
        else:
            relpath = os.path.relpath(
                os.path.join(self.path, os.path.relpath(path, self.obj.path)),
                self.root,
            )

        # check if relpath or its parents has a status
        tmppath = relpath
        while tmppath:
            if tmppath in self.rootvcs.status_subpaths:
                return self.rootvcs.status_subpaths[tmppath]
            tmppath = os.path.dirname(tmppath)

        # check if path contains some file in status
        if is_directory:
            statuses = set(status for subpath, status in self.rootvcs.status_subpaths.items()
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

class VcsThread(threading.Thread):
    """Vcs thread"""
    def __init__(self, ui, idle_delay):
        super(VcsThread, self).__init__()
        self.daemon = True
        self.ui = ui
        self.delay = idle_delay
        self.wake = threading.Event()

    def _check(self):
        """Check for hinders"""
        for column in self.ui.browser.columns:
            if column.target and column.target.is_directory and column.target.flat:
                return True
        return False

    def run(self):
        roots = set() # already updated roots
        redraw = False
        while True:
            if self._check():
                self.wake.wait(timeout=self.delay)
                self.wake.clear()
                continue

            for column in self.ui.browser.columns:
                target = column.target
                if target and target.is_directory and target.vcs:
                    # Redraw if tree is purged
                    if not target.vcs.check():
                        redraw = True
                    if target.vcs.track and target.vcs.root not in roots:
                        roots.add(target.vcs.root)
                        # Do not update repo when repodir is displayed (causes strobing)
                        if tuple(clmn for clmn in self.ui.browser.columns
                                 if clmn.target
                                 and (clmn.target.path == target.vcs.repodir or
                                      clmn.target.path.startswith(target.vcs.repodir + '/'))):
                            continue
                        if target.vcs.update_root():
                            target.vcs.update_tree()
                            redraw = True

            if redraw:
                redraw = False
                for column in self.ui.browser.columns:
                    if column.target and column.target.is_directory:
                        column.need_redraw = True
                self.ui.status.need_redraw = True
                if self.wake.is_set():
                    self.ui.redraw()

            roots.clear()
            self.wake.clear()
            self.wake.wait(timeout=self.delay)

    def wakeup(self):
        """Wakeup thread"""
        self.wake.set()

# Backend imports
import ranger.ext.vcs.git
import ranger.ext.vcs.hg
import ranger.ext.vcs.bzr
import ranger.ext.vcs.svn
