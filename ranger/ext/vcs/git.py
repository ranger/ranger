# -*- coding: utf-8 -*-
# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# Author: Abdó Roig-Maranges <abdo.roig@gmail.com>, 2011-2012
#
# vcs - a python module to handle various version control systems

import os
import re
import shutil
from datetime import datetime
import json

from ranger.ext.vcs import Vcs, VcsError

class Git(Vcs):
    """VCS implementation for Git"""
    vcsname = 'git'
    _status_combinations = (
        ('MADRC', ' ', 'staged'),
        (' MADRC', 'M', 'changed'),
        (' MARC', 'D', 'deleted'),

        ('D', 'DU', 'conflict'),
        ('A', 'AU', 'conflict'),
        ('U', 'ADU', 'conflict'),

        ('?', '?', 'untracked'),
        ('!', '!', 'ignored'),
    )

    # Auxiliar stuff
    #---------------------------

    def _git(self, args, path=None, silent=True, catchout=False, bytes=False):
        """Call git"""
        return self._vcs(path if path else self.path, 'git', args, silent=silent,
                         catchout=catchout, bytes=bytes)

    def _has_head(self):
        """Checks whether repo has head"""
        try:
            self._git(['rev-parse', 'HEAD'], silent=True)
        except VcsError:
            return False
        return True

    def _head_ref(self):
        """Gets HEAD's ref"""
        return self._git(['symbolic-ref', self.HEAD], catchout=True, silent=True) or None

    def _remote_ref(self, ref):
        """Gets remote ref associated to given ref"""
        if ref is None:
            return None
        return self._git(['for-each-ref', '--format=%(upstream)', ref],
                         catchout=True, silent=True) \
            or None

    def _sanitize_rev(self, rev):
        """Sanitize revision string"""
        if rev is None:
            return None
        return rev.strip()

    def _log(self, refspec=None, maxres=None, filelist=None):
        """Gets a list of dicts containing revision info, for the revisions matching refspec"""
        args = [
            '--no-pager', 'log',
            '--pretty={"short": "%h", "revid": "%H", "author": "%an", "date": %ct, "summary": "%s"}'
        ]
        if refspec:
            args += ['-1', refspec]
        elif maxres:
            args += ['-{0:d}'.format(maxres)]
        if filelist:
            args += ['--'] + filelist

        log = []
        for line in self._git(args, catchout=True).splitlines():
            line = json.loads(line)
            line['date'] = datetime.fromtimestamp(line['date'])
            log.append(line)
        return log

    def _git_file_status(self, code):
        """Translate git status code"""
        for X, Y, status in self._status_combinations:
            if code[0] in X and code[1] in Y:
                return status
        return 'unknown'

    # Repo creation
    #---------------------------

    def init(self):
        """Initializes a repo in current path"""
        self._git(['init'])
        self.update()

    def clone(self, src):
        """Clones a repo from src"""
        try:
            os.rmdir(self.path)
        except OSError:
            raise VcsError("Can't clone to {0:s}: Not an empty directory".format(self.path))

        self._git(['clone', src, os.path.basename(self.path)], path=os.path.dirname(self.path))
        self.update()

    # Action interface
    #---------------------------

    def commit(self, message):
        """Commits with a given message"""
        self._git(['commit', '--message', message])

    def add(self, filelist=None):
        """Adds files to the index, preparing for commit"""
        if filelist:
            self._git(['add', '--all'] + filelist)
        else:
            self._git(['add', '--all'])

    def reset(self, filelist=None):
        """Removes files from the index"""
        if filelist:
            self._git(['reset'] + filelist)
        else:
            self._git(['reset'])

    def pull(self, *args):
        """Pulls from remote"""
        self._git(['pull'] + list(args))

    def push(self, *args):
        """Pushes to remote"""
        self._git(['push'] + list(args))

    def checkout(self, rev):
        """Checks out a branch or revision"""
        self._git(['checkout', self._sanitize_rev(rev)])

    def extract_file(self, rev, name, dest):
        """Extracts a file from a given revision and stores it in dest dir"""
        if rev == self.INDEX:
            shutil.copyfile(os.path.join(self.path, name), dest)
        else:
            with open(dest, 'wb') as fd:
                fd.write(
                    self._git([
                        '--no-pager', 'show', '{0:s}:{1:s}'.format(self._sanitize_rev(rev), name)
                    ], catchout=True, bytes=True)
                )

    # Data Interface
    #---------------------------

    def get_status_allfiles(self):
        """Returs a dict (path: status) for paths not in sync. Strips trailing '/' from dirs"""
        statuses = {}
        skip = False
        for line in self._git(['status', '--porcelain', '-z'], catchout=True, bytes=True)\
                .decode('utf-8').split('\x00')[:-1]:
            if skip:
                skip = False
                continue
            statuses[os.path.normpath(line[3:])] = self._git_file_status(line[:2])
            if line.startswith('R'):
                skip = True
        return statuses

    def get_ignore_allfiles(self):
        """Returns a set of all the ignored files in the repo. Strips trailing '/' from dirs."""
        return set(
            os.path.normpath(p)
            for p in self._git(
                ['ls-files', '--others', '--directory', '--ignored', '--exclude-standard', '-z'],
                catchout=True, bytes=True
            ).decode('utf-8').split('\x00')[:-1]
        )

    def get_remote_status(self):
        """Checks the status of the repo regarding sync state with remote branch"""
        try:
            head = self._head_ref()
            remote = self._remote_ref(head)
        except VcsError:
            head = remote = None
        if not head or not remote:
            return 'none'

        output = self._git(['rev-list', '--left-right', '{0:s}...{1:s}'.format(remote, head)],
                           catchout=True)
        ahead = re.search("^>", output, flags=re.MULTILINE)
        behind = re.search("^<", output, flags=re.MULTILINE)
        if ahead:
            return 'diverged' if behind else 'ahead'
        else:
            return 'behind' if behind else 'sync'

    def get_branch(self):
        """Returns the current named branch, if this makes sense for the backend. None otherwise"""
        try:
            head = self._head_ref()
        except VcsError:
            head = None
        if head is None:
            return 'detached'

        match = re.match('refs/heads/([^/]+)', head)
        if match:
            return match.group(1)
        else:
            return None

    def get_log(self, filelist=None, maxres=None):
        """Get the entire log for the current HEAD"""
        if not self._has_head():
            return []
        return self._log(refspec=None, maxres=maxres, filelist=filelist)

    def get_raw_log(self, filelist=None):
        """Gets the raw log as a string"""
        if not self._has_head():
            return []
        args = ['log']
        if filelist:
            args += ['--'] + filelist
        return self._git(args, catchout=True)

    def get_raw_diff(self, refspec=None, filelist=None):
        """Gets the raw diff as a string"""
        args = ['diff']
        if refspec:
            args += [refspec]
        if filelist:
            args += ['--'] + filelist
        return self._git(args, catchout=True)

    def get_remote(self):
        """Returns the url for the remote repo attached to head"""
        if self.is_repo():
            try:
                ref = self._head_ref()
                remote = self._remote_ref(ref)
            except VcsError:
                ref = remote = None
            if not remote:
                return None

            match = re.match('refs/remotes/([^/]+)/', remote)
            if match:
                return self._git(['config', '--get', 'remote.{0:s}.url'.format(match.group(1))],
                                 catchout=True).strip() \
                    or None
        return None


    def get_revision_id(self, rev=None):
        """Get a canonical key for the revision rev"""
        if rev is None:
            rev = self.HEAD
        elif rev == self.INDEX:
            return None
        rev = self._sanitize_rev(rev)

        return self._sanitize_rev(self._git(['rev-parse', rev], catchout=True))

    def get_info(self, rev=None):
        """Gets info about the given revision rev"""
        if rev is None:
            rev = self.HEAD
        rev = self._sanitize_rev(rev)
        if rev == self.HEAD and not self._has_head():
            return None

        log = self._log(refspec=rev)
        if len(log) == 0:
            raise VcsError("Revision {0:s} does not exist".format(rev))
        elif len(log) > 1:
            raise VcsError("More than one instance of revision {0:s} ?!?".format(rev))
        else:
            return log[0]

    def get_files(self, rev=None):
        """Gets a list of files in revision rev"""
        if rev is None:
            rev = self.HEAD
        rev = self._sanitize_rev(rev)
        if rev is None:
            return []

        if rev == self.INDEX:
            return self._git(['ls-files', '-z'],
                             catchout=True, bytes=True).decode('utf-8').split('\x00')
        else:
            return self._git(['ls-tree', '--name-only', '-r', '-z', rev],
                             catchout=True, bytes=True).decode('utf-8').split('\x00')

# vim: expandtab:shiftwidth=4:tabstop=4:softtabstop=4:textwidth=80
