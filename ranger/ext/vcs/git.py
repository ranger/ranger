# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""Git module"""

from datetime import datetime
import json
import os
import re

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

    def _head_ref(self):
        """Returns HEAD reference"""
        return self._run(['symbolic-ref', self.HEAD]).rstrip('\n') or None

    def _remote_ref(self, ref):
        """Returns remote reference associated to given ref"""
        if ref is None:
            return None
        return self._run(['for-each-ref', '--format=%(upstream)', ref]).rstrip('\n') or None

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
            output = self._run(args).rstrip('\n')
        except VcsError:
            return None
        if not output:
            return None

        log = []
        for line in output\
                .replace('\\', '\\\\').replace('"', '\\"').replace('\x00', '"').split('\n'):
            line = json.loads(line)
            line['date'] = datetime.fromtimestamp(line['date'])
            log.append(line)
        return log

    def _status_translate(self, code):
        """Translate status code"""
        for code_x, code_y, status in self._status_translations:
            if code[0] in code_x and code[1] in code_y:
                return status
        return 'unknown'

    # Action interface

    def action_add(self, filelist=None):
        args = ['add', '--all']
        if filelist:
            args += ['--'] + filelist
        self._run(args, catchout=False)

    def action_reset(self, filelist=None):
        args = ['reset']
        if filelist:
            args += ['--'] + filelist
        self._run(args, catchout=False)

    # Data Interface

    def data_status_root(self):
        statuses = set()

        # Paths with status
        skip = False
        output = self._run(['status', '--porcelain', '-z']).rstrip('\x00')
        if not output:
            return 'sync'
        for line in output.split('\x00'):
            if skip:
                skip = False
                continue
            statuses.add(self._status_translate(line[:2]))
            if line.startswith('R'):
                skip = True

        for status in self.DIRSTATUSES:
            if status in statuses:
                return status
        return 'sync'

    def data_status_subpaths(self):
        statuses = {}

        # Ignored directories
        output = self._run([
            'ls-files', '-z', '--others', '--directory', '--ignored', '--exclude-standard'
        ]).rstrip('\x00')
        if output:
            for path in output.split('\x00'):
                if path.endswith('/'):
                    statuses[os.path.normpath(path)] = 'ignored'

        # Empty directories
        output = self._run(
            ['ls-files', '-z', '--others', '--directory', '--exclude-standard']).rstrip('\x00')
        if output:
            for path in output.split('\x00'):
                if path.endswith('/'):
                    statuses[os.path.normpath(path)] = 'none'

        # Paths with status
        output = self._run(['status', '--porcelain', '-z', '--ignored']).rstrip('\x00')
        if output:
            skip = False
            for line in output.split('\x00'):
                if skip:
                    skip = False
                    continue
                statuses[os.path.normpath(line[3:])] = self._status_translate(line[:2])
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

        output = self._run(['rev-list', '--left-right', '{0:s}...{1:s}'.format(remote, head)])
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
        return match.group(1) if match else None

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
            raise VcsError('More than one instance of revision {0:s}'.format(rev))
