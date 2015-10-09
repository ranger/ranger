# -*- coding: utf-8 -*-
# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# Author: Abdó Roig-Maranges <abdo.roig@gmail.com>, 2011-2012
#
# vcs - a python module to handle various version control systems
"""Vcs module"""

import os
import subprocess

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
    vcsname = None

    # Possible status responses in order of importance
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
    REMOTE_STATUS = (
        'diverged',
        'behind',
        'ahead',
        'sync',
        'none',
        'unknown',
    )

    def __init__(self, directoryobject):
        self.repotypes = {
            'git': ranger.ext.vcs.git.Git,
            'hg': ranger.ext.vcs.hg.Hg,
            'bzr': ranger.ext.vcs.bzr.Bzr,
            'svn': ranger.ext.vcs.svn.SVN,
        }

        self.path = directoryobject.path
        self.repotypes_settings = [
            repotype for repotype, setting in \
            (
                ('git', directoryobject.settings.vcs_backend_git),
                ('hg', directoryobject.settings.vcs_backend_hg),
                ('bzr', directoryobject.settings.vcs_backend_bzr),
                ('svn', directoryobject.settings.vcs_backend_svn),
            )
            if setting in ('enabled', 'local')
        ]

        self.status_subpaths = {}
        self.head = None
        self.remotestatus = None
        self.branch = None

        self.root, self.repodir, self.repotype = self.find_root(self.path)
        self.is_root = True if self.path == self.root else False

        if self.root:
            self.track = True
            self.__class__ = self.repotypes[self.repotype]

            if not os.access(self.repodir, os.R_OK):
                self.track = False
                if self.is_root:
                    directoryobject.vcspathstatus = 'unknown'
                    self.remotestatus = 'unknown'
            # Do not track self.repodir or its subpaths
            if self.path == self.repodir or self.path.startswith(self.repodir + '/'):
                self.track = False
        else:
            self.track = False

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
        while True:
            repodir, repotype = self.get_repotype(path)
            if repodir:
                return (path, repodir, repotype)
            if path == '/':
                break
            path = os.path.dirname(path)
        return (None, None, None)

    def update(self, directoryobject, child=False):
        """Update repository"""
        if not os.path.exists(self.repodir):
            self.__init__(directoryobject)
            if not self.root:
                directoryobject.vcspathstatus = None
                return

        root = self if self.is_root else directoryobject.fm.get_directory(self.root).vcs
        if child and self.is_root:
            directoryobject.vcspathstatus = self.get_status_root_child()
        elif not child:
            root.head = root.get_info(root.HEAD)
            root.branch = root.get_branch()
            root.status_subpaths = root.get_status_subpaths()
            if self.is_root:
                directoryobject.vcspathstatus = self.get_status_root()

        if self.is_root:
            root.remotestatus = root.get_status_remote()
        else:
            self.head = root.head
            self.branch = root.branch
            self.status_subpaths = root.status_subpaths
            directoryobject.vcspathstatus = root.get_status_subpath(
                self.path, is_directory=True)

    # Repo creation
    #---------------------------

    def init(self, repotype):
        """Initializes a repo in current path"""
        if not repotype in self.repo_types:
            raise VcsError("Unrecognized repo type {0:s}".format(repotype))

        if not os.path.exists(self.path):
            os.makedirs(self.path)
        try:
            self.__class__ = self.repo_types[repotype]
            self.init()
        except:
            self.__class__ = Vcs
            raise

    def clone(self, repotype, src):
        """Clones a repo from src"""
        if not repotype in self.repo_types:
            raise VcsError("Unrecognized repo type {0:s}".format(repotype))

        if not os.path.exists(self.path):
            os.makedirs(self.path)
        try:
            self.__class__ = self.repo_types[repotype]
            self.clone(src)
        except:
            self.__class__ = Vcs
            raise

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

    def is_repo(self):
        """Checks wether there is an initialized repo in self.path"""
        return self.path and os.path.exists(self.path) and self.root is not None

    def is_tracking(self):
        """Checks whether HEAD is tracking a remote repo"""
        return self.get_remote(self.HEAD) is not None

    def get_status_root_child(self):
        """Returns the status of a child root, very cheap"""
        raise NotImplementedError

    def get_status_root(self):
        """Returns the status of root"""
        statuses = set(status for path, status in self.status_subpaths.items())
        for status in self.DIR_STATUS:
            if status in statuses:
                return status
        return 'sync'

    def get_status_subpath(self, path, is_directory=False):
        """Returns the status of path"""
        relpath = os.path.relpath(path, self.root)

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
            for status in self.DIR_STATUS:
                if status in statuses:
                    return status
        return 'sync'

    def get_status_subpaths(self):
        """Returns a dict indexed by subpaths not in sync their status as values.
           Paths are given relative to the root.  Strips trailing '/' from dirs."""
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

import ranger.ext.vcs.git
import ranger.ext.vcs.hg
import ranger.ext.vcs.bzr
import ranger.ext.vcs.svn
