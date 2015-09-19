# -*- coding: utf-8 -*-
# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# Author: Abdó Roig-Maranges <abdo.roig@gmail.com>, 2011-2012
#
# vcs - a python module to handle various version control systems

import os
import subprocess
from datetime import datetime


class VcsError(Exception):
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
    INDEX    = "INDEX"
    HEAD     = "HEAD"
    NONE     = "NONE"
    vcsname  = None

    # Possible status responses
    FILE_STATUS   = ['conflict', 'untracked', 'deleted', 'changed', 'staged', 'ignored', 'sync', 'none', 'unknown']
    REMOTE_STATUS = ['none', 'sync', 'behind', 'ahead', 'diverged', 'unknown']


    def __init__(self, path, vcstype=None):
        # This is a bit hackish, but I need to import here to avoid circular imports
        from .git import Git
        from .hg  import Hg
        from .bzr import Bzr
        from .svn import SVN
        self.repo_types  = {'git': Git, 'hg': Hg, 'bzr': Bzr, 'svn': SVN}

        self.path = os.path.expanduser(path)
        self.status = {}
        self.ignored = set()
        self.root = None

        self.update(vcstype=vcstype)


    # Auxiliar
    #---------------------------

    def _vcs(self, path, cmd, args, silent=False, catchout=False, bytes=False):
        """Executes a vcs command"""
        with open('/dev/null', 'w') as devnull:
            if silent: out=devnull
            else:      out=None
            try:
                if catchout:
                    raw = subprocess.check_output([cmd] + args, stderr=out, cwd=path)
                    if bytes: return raw
                    else:     return raw.decode('utf-8', errors="ignore").strip()
                else:
                    subprocess.check_call([cmd] + args, stderr=out, stdout=out, cwd=path)
            except subprocess.CalledProcessError:
                raise VcsError("%s error on %s. Command: %s" % (cmd, path, ' '.join([cmd] + args)))


    def _path_contains(self, parent, path):
        """Checks wether path is an object belonging to the subtree in parent"""
        if parent == path: return True
        parent = os.path.normpath(parent + '/')
        path = os.path.normpath(path)
        return os.path.commonprefix([parent, path]) == parent


    # Object manipulation
    #---------------------------
    # This may be a little hacky, but very useful. An instance of Vcs class changes its own class
    # when calling update(), to match the right repo type. I can have the same object adapt to
    # the path repo type, if this ever changes!

    def get_repo_type(self, path):
        """Returns the right repo type for path. None if no repo present in path"""
        for rn, rt in self.repo_types.items():
            if path and os.path.exists(os.path.join(path, '.%s' % rn)): return rt
        return None


    def get_root(self, path):
        """Finds the repository root path. Otherwise returns none"""
        curpath = os.path.abspath(path)
        while curpath != '/':
            if self.get_repo_type(curpath): return curpath
            else:                           curpath = os.path.dirname(curpath)
        return None


    def update(self, vcstype=None):
        """Updates the repo instance. Re-checks the repo and changes object class if repo type changes
           If vcstype is given, uses that repo type, without autodetection"""
        if os.path.exists(self.path):
            self.root = self.get_root(self.path)
            if vcstype:
                if vcstype in self.repo_types:
                    ty = self.repo_types[vcstype]
                else:
                    raise VcsError("Unrecognized repo type %s" % vcstype)
            else:
                ty = self.get_repo_type(self.root)
            if ty:
                self.__class__ = ty
                return

        self.__class__ = Vcs


    # Repo creation
    #---------------------------

    def init(self, repotype):
        """Initializes a repo in current path"""
        if not repotype in self.repo_types:
            raise VcsError("Unrecognized repo type %s" % repotype)

        if not os.path.exists(self.path): os.makedirs(self.path)
        rt = self.repo_types[repotype]
        try:
            self.__class__ = rt
            self.init()
        except:
            self.__class__ = Vcs
            raise


    def clone(self, repotype, src):
        """Clones a repo from src"""
        if not repotype in self.repo_types:
            raise VcsError("Unrecognized repo type %s" % repotype)

        if not os.path.exists(self.path): os.makedirs(self.path)
        rt = self.repo_types[repotype]
        try:
            self.__class__ = rt
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


    def pull(self):
        """Pulls from remote"""
        raise NotImplementedError


    def push(self):
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
        return self.path and os.path.exists(self.path) and self.root != None


    def is_tracking(self):
        """Checks whether HEAD is tracking a remote repo"""
        return self.get_remote(self.HEAD) != None


    def get_file_status(self, path):
        """Returns the status for a given path regarding the repo"""

        # if path is relative, join it with root. otherwise do nothing
        path = os.path.join(self.root, path)

        # path is not in the repo
        if not self._path_contains(self.root, path):
            return "none"

        # check if prel or some parent of prel is ignored
        prel = os.path.relpath(path, self.root)
        while len(prel) > 0 and prel != '/' and prel != '.':
            if prel in self.ignored: return "ignored"
            prel, tail = os.path.split(prel)

        # check if prel or some parent of prel is listed in status
        prel = os.path.relpath(path, self.root)
        while len(prel) > 0 and prel != '/' and prel != '.':
            if prel in self.status: return self.status[prel]
            prel, tail = os.path.split(prel)

        # check if prel is a directory that contains some file in status
        prel = os.path.relpath(path, self.root)
        if os.path.isdir(path):
            sts = set(st for p, st in self.status.items()
                      if self._path_contains(path, os.path.join(self.root, p)))
            for st in self.FILE_STATUS:
                if st in sts: return st

        # it seems prel is in sync
        return "sync"


    def get_status(self, path=None):
        """Returns a dict with changed files under path and their status.
           If path is None, returns all changed files"""

        self.status = self.get_status_allfiles()
        self.ignored = self.get_ignore_allfiles()
        if path:
            path = os.path.join(self.root, path)
            if os.path.commonprefix([self.root, path]) == self.root:
                return dict((p, st) for p, st in self.status.items() if self._path_contains(path, os.path.join(self.root, p)))
            else:
                return {}
        else:
            return self.status


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



    # I / O
    #---------------------------

    def print_log(self, fmt):
        log = self.log()
        if fmt == "compact":
            for dt in log:
                print(self.format_revision_compact(dt))
        else:
            raise Exception("Unknown format %s" % fmt)


    def format_revision_compact(self, dt):
        return "{0:<10}{1:<20}{2}".format(dt['revshort'],
                                          dt['date'].strftime('%a %b %d, %Y'),
                                          dt['summary'])


    def format_revision_text(self, dt):
        L = ["revision:         %s:%s" % (dt['revshort'], dt['revhash']),
             "date:             %s" % dt['date'].strftime('%a %b %d, %Y'),
             "time:             %s" % dt['date'].strftime('%H:%M'),
             "user:             %s" % dt['author'],
             "description:      %s" % dt['summary']]
        return '\n'.join(L)
