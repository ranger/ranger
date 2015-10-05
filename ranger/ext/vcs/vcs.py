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
    FILE_STATUS = (
        'conflict',
        'untracked',
        'deleted',
        'changed',
        'staged',
        'ignored',
        'sync',
        'none',
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
        from ranger.ext.vcs.git import Git
        from ranger.ext.vcs.hg import Hg
        from ranger.ext.vcs.bzr import Bzr
        from ranger.ext.vcs.svn import SVN
        self.repotypes = {
            'git': Git,
            'hg': Hg,
            'bzr': Bzr,
            'svn': SVN,
        }

        self.path = directoryobject.path
        self.repotypes_settings = [
            repotype for repotype, setting in \
            (
                ('git', directoryobject.settings.vcs_backend_git),
                ('hg', directoryobject.settings.vcs_backend_git),
                ('bzr', directoryobject.settings.vcs_backend_git),
                ('svn', directoryobject.settings.vcs_backend_git),
            )
            if setting in ('enabled', 'local')
        ]

        self.status = {}
        self.ignored = set()
        self.head = None
        self.remotestatus = None
        self.branch = None

        self.root, self.repotype = self.find_root(self.path)
        self.is_root = True if self.path == self.root else False

        if self.root:
            # Do not track the repo data directory
            repodir = os.path.join(self.root, '.{0:s}'.format(self.repotype))
            if self.path == repodir or self.path.startswith(repodir + '/'):
                self.root = None
                return
            if self.is_root:
                self.root = self.path
                self.__class__ = self.repotypes[self.repotype]
            else:
                root = directoryobject.fm.get_directory(self.root)
                self.repotype = root.vcs.repotype
                self.__class__ = root.vcs.__class__

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
            if os.path.exists(os.path.join(path, '.{0:s}'.format(repotype))):
                return repotype
        return None

    def find_root(self, path):
        """Finds the repository root path. Otherwise returns none"""
        while True:
            repotype = self.get_repotype(path)
            if repotype:
                return (path, repotype)
            if path == '/':
                break
            path = os.path.dirname(path)
        return (None, None)

    def update(self, directoryobject):
        """Update repository"""
        if self.is_root:
            self.head = self.get_info(self.HEAD)
            self.branch = self.get_branch()
            self.remotestatus = self.get_remote_status()
            self.status = self.get_status_allfiles()
            self.ignored = self.get_ignore_allfiles()
            directoryobject.vcsfilestatus = self.get_root_status()
        else:
            root = directoryobject.fm.get_directory(self.root)
            self.head = root.vcs.head = root.vcs.get_info(root.vcs.HEAD)
            self.branch = root.vcs.branch = root.vcs.get_branch()
            self.status = root.vcs.status = root.vcs.get_status_allfiles()
            self.ignored = root.vcs.ignored = root.vcs.get_ignore_allfiles()
            directoryobject.vcsfilestatus = root.vcs.get_path_status(
                self.path, is_directory=True)

    def update_child(self, directoryobject):
        """After update() for subdirectories"""
        root = directoryobject.fm.get_directory(self.root)
        self.head = root.vcs.head
        self.branch = root.vcs.branch
        self.status = root.vcs.status
        self.ignored = root.vcs.ignored
        directoryobject.vcsfilestatus = root.vcs.get_path_status(
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

    def get_root_status(self):
        """Returns the status of root"""
        statuses = set(
            status for path, status in self.status.items()
        )
        for status in self.FILE_STATUS:
            if status in statuses:
                return status
        return 'sync'

    def get_path_status(self, path, is_directory=False):
        """Returns the status of path"""
        relpath = os.path.relpath(path, self.root)

        # check if relpath or its parents has a status
        tmppath = relpath
        while tmppath:
            if tmppath in self.ignored:
                return 'ignored'
            elif tmppath in self.status:
                return self.status[tmppath]
            tmppath = os.path.dirname(tmppath)

        # check if path contains some file in status
        if is_directory:
            statuses = set(
                status for path, status in self.status.items()
                if path.startswith(relpath + '/')
            )
            for status in self.FILE_STATUS:
                if status in statuses:
                    return status

        return 'sync'

    def get_status_allfiles(self):
        """Returns a dict indexed by files not in sync their status as values.
           Paths are given relative to the root.  Strips trailing '/' from dirs."""
        raise NotImplementedError

    def get_ignore_allfiles(self):
        """Returns a set of all the ignored files in the repo. Strips trailing '/' from dirs."""
        raise NotImplementedError

    def get_remote_status(self):
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
