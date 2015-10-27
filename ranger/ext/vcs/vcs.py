# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# Author: Abdó Roig-Maranges <abdo.roig@gmail.com>, 2011-2012
#
# vcs - a python module to handle various version control systems
"""Vcs module"""

import os
import subprocess
import threading

class VcsError(Exception):
    """Vcs exception"""
    pass

class Vcs(object):
    """ This class represents a version controlled path, abstracting the usual
        operations from the different supported backends.

        The backends are declared in te variable self.repo_types, and are derived
        classes from Vcs with the following restrictions:

         * do NOT implement __init__. Vcs takes care of this.

         * do not create change internal state. All internal state should be
           handled in Vcs

        Objects from backend classes should never be created directly. Instead
        create objects of Vcs class. The initialization calls update, which takes
        care of detecting the right Vcs backend to use and dynamically changes the
        object type accordingly.
        """

    # These are abstracted revs, representing the current index (staged files),
    # the current head and nothing. Every backend should redefine them if the
    # version control has a similar concept, or implement _sanitize_rev method to
    # clean the rev before using them
    INDEX = 'INDEX'
    HEAD = 'HEAD'
    NONE = 'NONE'

    REPOTYPES = {
        'git': {'class': 'Git', 'setting': 'vcs_backend_git'},
        'hg': {'class': 'Hg', 'setting': 'vcs_backend_hg'},
        'bzr': {'class': 'Bzr', 'setting': 'vcs_backend_bzr'},
        'svn': {'class': 'SVN', 'setting': 'vcs_backend_svn'},
    }

    # Possible directory statuses in order of importance with statuses that
    # don't make sense disabled
    DIR_STATUS = (
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

        self.root, self.repodir, self.repotype, self.links = self.find_root(self.path)
        self.is_root = True if self.obj.path == self.root else False

        if self.root:
            if self.is_root:
                self.rootvcs = self
                self.__class__ = getattr(getattr(ranger.ext.vcs, self.repotype),
                                         self.REPOTYPES[self.repotype]['class'])
                self.status_subpaths = {}

                if not os.access(self.repodir, os.R_OK):
                    directoryobject.vcspathstatus = 'unknown'
                    self.remotestatus = 'unknown'
                    return

                try:
                    self.head = self.get_info(self.HEAD)
                    self.branch = self.get_branch()
                    self.remotestatus = self.get_status_remote()
                    self.obj.vcspathstatus = self.get_status_root_cheap()
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

    # Auxiliar
    #---------------------------

    def _vcs(self, path, cmd, args, silent=False, catchout=False, bytes=False):
        """Executes a vcs command"""
        with open(os.devnull, 'w') as devnull:
            out = devnull if silent else None
            try:
                if catchout:
                    output = subprocess.check_output([cmd] + args, stderr=out, cwd=path)
                    return output if bytes else output.decode('utf-8').strip()
                else:
                    subprocess.check_call([cmd] + args, stderr=out, stdout=out, cwd=path)
            except subprocess.CalledProcessError:
                raise VcsError("{0:s} error on {1:s}. Command: {2:s}"\
                               .format(cmd, path, ' '.join([cmd] + args)))
            except FileNotFoundError:
                raise VcsError("{0:s} error on {1:s}: File not found".format(cmd, path))

    # Generic
    #---------------------------

    def get_repotype(self, path):
        """Returns the right repo type for path. None if no repo present in path"""
        for repotype in self.repotypes_settings:
            repodir = os.path.join(path, '.{0:s}'.format(repotype))
            if os.path.exists(repodir):
                return (repodir, repotype)
        return (None, None)

    def find_root(self, path):
        """Finds the repository root path. Otherwise returns none"""
        links = set()
        while True:
            if os.path.islink(path):
                links.add(path)
                relpath = os.path.relpath(self.path, path)
                path = os.path.realpath(path)
                self.path = os.path.normpath(os.path.join(path, relpath))
            repodir, repotype = self.get_repotype(path)
            if repodir:
                return (path, repodir, repotype, links)
            if path == '/':
                break
            path = os.path.dirname(path)
        return (None, None, None, None)

    def check(self):
        """Check repository health"""
        if not self.in_repodir \
                and (not self.track or (not self.is_root and self.get_repotype(self.path)[0])):
            self.__init__(self.obj)
        elif self.track and not os.path.exists(self.repodir):
            self.update_tree(purge=True)
            return False
        return True

    def update_root(self):
        """Update repository"""
        try:
            self.rootvcs.head = self.rootvcs.get_info(self.HEAD)
            self.rootvcs.branch = self.rootvcs.get_branch()
            self.rootvcs.status_subpaths = self.rootvcs.get_status_subpaths()
            self.rootvcs.remotestatus = self.rootvcs.get_status_remote()
            self.rootvcs.obj.vcspathstatus = self.rootvcs.get_status_root()
        except VcsError:
            self.update_tree(purge=True)
            return False
        return True

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
                            fileobj.vcspathstatus = None
                            fileobj.vcs.__init__(fileobj)
                        else:
                            fileobj.vcspathstatus = None
                        continue

                    if fileobj.is_directory:
                        fileobj.vcs.check()
                        if not fileobj.vcs.track:
                            continue
                        if not fileobj.vcs.is_root:
                            fileobj.vcspathstatus = wroot_obj.vcs.get_status_subpath(
                                fileobj.path, is_directory=True)
                    else:
                        fileobj.vcspathstatus = wroot_obj.vcs.get_status_subpath(fileobj.path)

            # Remove dead directories
            for wdir in wdirs.copy():
                try:
                    wdir_obj = self.obj.fm.directories[os.path.join(wroot, wdir)]
                except KeyError:
                    wdirs.remove(wdir)
                    continue
                if wdir_obj.vcs.is_root or not wdir_obj.vcs.track:
                    wdirs.remove(wdir)

    def update_tree(self, purge=False):
        """Update tree"""
        self._update_walk(self.root, purge)
        for path in self.rootvcs.links.copy():
            self._update_walk(path, purge)
            try:
                dirobj = self.obj.fm.directories[path]
            except KeyError:
                continue
            if purge:
                dirobj.vcspathstatus = None
                dirobj.vcs.__init__(dirobj.vcs.obj)
            elif dirobj.vcs.path == self.root:
                dirobj.vcspathstatus = self.rootvcs.get_status_root()
            else:
                dirobj.vcspathstatus = dirobj.vcs.get_status_subpath(
                    dirobj.path, is_directory=True)
        if purge:
            self.rootvcs.__init__(self.rootvcs.obj)

    # Action interface
    #---------------------------

    def commit(self, message):
        """Commits with a given message"""
        raise NotImplementedError

    def add(self, filelist):
        """Adds files to the index, preparing for commit"""
        raise NotImplementedError

    def reset(self, filelist):
        """Removes files from the index"""
        raise NotImplementedError

    def pull(self, **kwargs):
        """Pulls from remote"""
        raise NotImplementedError

    def push(self, **kwargs):
        """Pushes to remote"""
        raise NotImplementedError

    def checkout(self, rev):
        """Checks out a branch or revision"""
        raise NotImplementedError

    def extract_file(self, rev, name, dest):
        """Extracts a file from a given revision and stores it in dest dir"""
        raise NotImplementedError

    # Data
    #---------------------------

    def get_status_root_cheap(self):
        """Returns the status of self.root, very cheap"""
        raise NotImplementedError

    def get_status_root(self):
        """Returns the status of root"""
        statuses = set(status for path, status in self.status_subpaths.items())
        for status in self.DIR_STATUS:
            if status in statuses:
                return status
        return 'sync'

    def get_status_subpath(self, path, is_directory=False):
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
            for status in self.DIR_STATUS:
                if status in statuses:
                    return status
        return 'sync'

    def get_status_subpaths(self):
        """Returns a dict indexed by subpaths not in sync their status as values.
           Paths are given relative to self.root.  Strips trailing '/' from dirs."""
        raise NotImplementedError

    def get_status_remote(self):
        """Checks the status of the entire repo"""
        raise NotImplementedError

    def get_branch(self):
        """Returns the current named branch, if this makes sense for the backend. None otherwise"""
        raise NotImplementedError

    def get_log(self):
        """Get the entire log for the current HEAD"""
        raise NotImplementedError

    def get_raw_log(self, filelist=None):
        """Gets the raw log as a string"""
        raise NotImplementedError

    def get_raw_diff(self, refspec=None, filelist=None):
        """Gets the raw diff as a string"""
        raise NotImplementedError

    def get_remote(self):
        """Returns the url for the remote repo attached to head"""
        raise NotImplementedError

    def get_revision_id(self, rev=None):
        """Get a canonical key for the revision rev"""
        raise NotImplementedError

    def get_info(self, rev=None):
        """Gets info about the given revision rev"""
        raise NotImplementedError

    def get_files(self, rev=None):
        """Gets a list of files in revision rev"""
        raise NotImplementedError

class VcsThread(threading.Thread):
    """Vcs thread"""
    def __init__(self, ui, idle_delay):
        super(VcsThread, self).__init__(daemon=True)
        self.ui = ui
        self.delay = idle_delay / 1000
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
                    if target.vcs.track and not target.vcs.root in roots:
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

import ranger.ext.vcs.git
import ranger.ext.vcs.hg
import ranger.ext.vcs.bzr
import ranger.ext.vcs.svn
