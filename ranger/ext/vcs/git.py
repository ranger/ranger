"""Git module"""

import os
import re
from datetime import datetime
import json

from .vcs import Vcs, VcsError

class Git(Vcs):
    """VCS implementation for Git"""
    _status_translations = (
        ('MADRC', ' ', 'staged'),
        (' MADRC', 'M', 'changed'),
        (' MARC', 'D', 'deleted'),

        ('D', 'DU', 'conflict'),
        ('A', 'AU', 'conflict'),
        ('U', 'ADU', 'conflict'),

        ('?', '?', 'untracked'),
        ('!', '!', 'ignored'),
    )

    # Generic
    #---------------------------

    def _git(self, args, path=None, silent=True, catchout=False, bytes=False):
        """Call git"""
        return self._vcs(path or self.path, 'git', args, silent=silent,
                         catchout=catchout, bytes=bytes)

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

    def _log(self, refspec=None, maxres=None, filelist=None):
        """Gets a list of dicts containing revision info, for the revisions matching refspec"""
        args = [
            '--no-pager', 'log',
            '--pretty={'
            '%x00short%x00:%x00%h%x00,'
            '%x00revid%x00: %x00%H%x00,'
            '%x00author%x00: %x00%an <%ae>%x00, %x00date%x00: %ct, %x00summary%x00: %x00%s%x00'
            '}'
        ]
        if refspec:
            args += ['-1', refspec]
        elif maxres:
            args += ['-{0:d}'.format(maxres)]
        if filelist:
            args += ['--'] + filelist

        try:
            log_raw = self._git(args, catchout=True)\
                .replace('\\', '\\\\').replace('"', '\\"').replace('\x00', '"').splitlines()
        except VcsError:
            return []

        log = []
        for line in log_raw:
            line = json.loads(line)
            line['date'] = datetime.fromtimestamp(line['date'])
            log.append(line)
        return log

    def _git_status_translate(self, code):
        """Translate git status code"""
        for X, Y, status in self._status_translations:
            if code[0] in X and code[1] in Y:
                return status
        return 'unknown'

    # Action interface
    #---------------------------

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

    # Data Interface
    #---------------------------

    def get_status_root_cheap(self):
        """Returns the status of root, very cheap"""
        statuses = set()
        # Paths with status
        skip = False
        for line in self._git(['status', '--porcelain', '-z'],
                              catchout=True, bytes=True).decode('utf-8').split('\x00')[:-1]:
            if skip:
                skip = False
                continue
            statuses.add(self._git_status_translate(line[:2]))
            if line.startswith('R'):
                skip = True

        for status in self.DIR_STATUS:
            if status in statuses:
                return status
        return 'sync'

    def get_status_subpaths(self):
        """Returns a dict (path: status) for paths not in sync. Strips trailing '/' from dirs"""
        statuses = {}

        # Ignored directories
        for line in self._git(
                ['ls-files', '-z', '--others', '--directory', '--ignored', '--exclude-standard'],
                catchout=True, bytes=True
        ).decode('utf-8').split('\x00')[:-1]:
            if line.endswith('/'):
                statuses[os.path.normpath(line)] = 'ignored'

        # Empty directories
        for line in self._git(
                ['ls-files', '-z', '--others', '--directory', '--exclude-standard'],
                catchout=True, bytes=True
        ).decode('utf-8').split('\x00')[:-1]:
            if line.endswith('/'):
                statuses[os.path.normpath(line)] = 'none'

        # Paths with status
        skip = False
        for line in self._git(['status', '--porcelain', '-z', '--ignored'],
                              catchout=True, bytes=True).decode('utf-8').split('\x00')[:-1]:
            if skip:
                skip = False
                continue
            statuses[os.path.normpath(line[3:])] = self._git_status_translate(line[:2])
            if line.startswith('R'):
                skip = True

        return statuses

    def get_status_remote(self):
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

    def get_info(self, rev=None):
        """Gets info about the given revision rev"""
        if rev is None:
            rev = self.HEAD

        log = self._log(refspec=rev)
        if len(log) == 0:
            if rev == self.HEAD:
                return None
            else:
                raise VcsError('Revision {0:s} does not exist'.format(rev))
        elif len(log) > 1:
            raise VcsError('More than one instance of revision {0:s} ?!?'.format(rev))
        else:
            return log[0]
