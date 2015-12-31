# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

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

    def _git(self, args, path=None, catchout=True, retbytes=False):
        """Run a git command"""
        return self._vcs(['git'] + args, path or self.path, catchout=catchout, retbytes=retbytes)

    def _head_ref(self):
        """Returns HEAD reference"""
        return self._git(['symbolic-ref', self.HEAD]).rstrip() or None

    def _remote_ref(self, ref):
        """Returns remote reference associated to given ref"""
        if ref is None:
            return None
        return self._git(['for-each-ref', '--format=%(upstream)', ref]).rstrip() or None

    def _log(self, refspec=None, maxres=None, filelist=None):
        """Returns an array of dicts containing revision info for refspec"""
        args = [
            '--no-pager', 'log',
            '--pretty={'
            '%x00short%x00:%x00%h%x00,'
            '%x00revid%x00:%x00%H%x00,'
            '%x00author%x00:%x00%an <%ae>%x00,'
            '%x00date%x00:%ct,'
            '%x00summary%x00:%x00%s%x00'
            '}'
        ]
        if refspec:
            args += ['-1', refspec]
        elif maxres:
            args += ['-{0:d}'.format(maxres)]
        if filelist:
            args += ['--'] + filelist

        try:
            output = self._git(args)\
                .replace('\\', '\\\\').replace('"', '\\"').replace('\x00', '"').splitlines()
        except VcsError:
            return None

        log = []
        for line in output:
            line = json.loads(line)
            line['date'] = datetime.fromtimestamp(line['date'])
            log.append(line)
        return log

    def _git_status_translate(self, code):
        """Translate status code"""
        for X, Y, status in self._status_translations:  # pylint: disable=invalid-name
            if code[0] in X and code[1] in Y:
                return status
        return 'unknown'

    # Action interface

    def action_add(self, filelist=None):
        args = ['add', '--all']
        if filelist:
            args += ['--'] + filelist
        self._git(args, catchout=False)

    def action_reset(self, filelist=None):
        args = ['reset']
        if filelist:
            args += ['--'] + filelist
        self._git(args, catchout=False)

    # Data Interface

    def data_status_root(self):
        statuses = set()

        # Paths with status
        skip = False
        for line in self._git(['status', '--porcelain', '-z']).split('\x00')[:-1]:
            if skip:
                skip = False
                continue
            statuses.add(self._git_status_translate(line[:2]))
            if line.startswith('R'):
                skip = True

        for status in self.DIRSTATUSES:
            if status in statuses:
                return status
        return 'sync'

    def data_status_subpaths(self):
        statuses = {}

        # Ignored directories
        for path in self._git(
                ['ls-files', '-z', '--others', '--directory', '--ignored', '--exclude-standard'])\
                .split('\x00')[:-1]:
            if path.endswith('/'):
                statuses[os.path.normpath(path)] = 'ignored'

        # Empty directories
        for path in self._git(['ls-files', '-z', '--others', '--directory', '--exclude-standard'])\
                .split('\x00')[:-1]:
            if path.endswith('/'):
                statuses[os.path.normpath(path)] = 'none'

        # Paths with status
        skip = False
        for line in self._git(['status', '--porcelain', '-z', '--ignored']).split('\x00')[:-1]:
            if skip:
                skip = False
                continue
            statuses[os.path.normpath(line[3:])] = self._git_status_translate(line[:2])
            if line.startswith('R'):
                skip = True

        return statuses

    def data_status_remote(self):
        try:
            head = self._head_ref()
            remote = self._remote_ref(head)
        except VcsError:
            head = remote = None
        if not head or not remote:
            return 'none'

        output = self._git(['rev-list', '--left-right', '{0:s}...{1:s}'.format(remote, head)])
        ahead = re.search(r'^>', output, flags=re.MULTILINE)
        behind = re.search(r'^<', output, flags=re.MULTILINE)
        if ahead:
            return 'diverged' if behind else 'ahead'
        else:
            return 'behind' if behind else 'sync'

    def data_branch(self):
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

    def data_info(self, rev=None):
        if rev is None:
            rev = self.HEAD

        log = self._log(refspec=rev)
        if not log:
            if rev == self.HEAD:
                return None
            else:
                raise VcsError('Revision {0:s} does not exist'.format(rev))
        elif len(log) == 1:
            return log[0]
        else:
            raise VcsError('More than one instance of revision {0:s} ?!?'.format(rev))
