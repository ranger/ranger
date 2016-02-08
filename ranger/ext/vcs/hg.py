# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""Mercurial module"""

from datetime import datetime
import json
import os

from .vcs import Vcs, VcsError


class Hg(Vcs):
    """VCS implementation for Mercurial"""
    HEAD = 'tip'

    _status_translations = (
        ('AR', 'staged'),
        ('M', 'changed'),
        ('!', 'deleted'),

        ('?', 'untracked'),
        ('I', 'ignored'),
    )

    # Generic

    def _log(self, refspec=None, maxres=None, filelist=None):

        args = [
            'log', '--template',
            '\\{'
            '\\x00short\\x00:\\x00{rev}\\x00,'
            '\\x00revid\\x00:\\x00{node}\\x00,'
            '\\x00author\\x00:\\x00{author}\\x00,'
            '\\x00date\\x00:\\x00{date}\\x00,'
            '\\x00summary\\x00:\\x00{desc}\\x00'
            '}\\n'
        ]
        if refspec:
            args += ['--limit', '1', '--rev', refspec]
        elif maxres:
            args += ['--limit', str(maxres)]
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
            line['date'] = datetime.fromtimestamp(float(line['date'].split('-')[0]))
            log.append(line)
        return log

    def _remote_url(self):
        """Remote url"""
        try:
            return self._run(['showconfig', 'paths.default']).rstrip('\n') or None
        except VcsError:
            return None

    def _status_translate(self, code):
        """Translate status code"""
        for code_x, status in self._status_translations:  # pylint: disable=invalid-name
            if code in code_x:
                return status
        return 'unknown'

    # Action interface

    def action_add(self, filelist=None):
        args = ['add']
        if filelist:
            args += ['--'] + filelist
        self._run(args, catchout=False)

    def action_reset(self, filelist=None):
        args = ['forget', '--']
        if filelist:
            args += filelist
        else:
            args += self.rootvcs.status_subpaths.keys()
        self._run(args, catchout=False)

    # Data interface

    def data_status_root(self):
        statuses = set()

        # Paths with status
        output = self._run(['status', '--all', '--print0']).rstrip('\x00')
        if not output:
            return 'sync'
        for line in output.split('\x00'):
            code = line[0]
            if code == 'C':
                continue
            statuses.add(self._status_translate(code))

        for status in self.DIRSTATUSES:
            if status in statuses:
                return status
        return 'sync'

    def data_status_subpaths(self):
        statuses = {}

        # Paths with status
        output = self._run(['status', '--all', '--print0']).rstrip('\x00')
        if output:
            for line in output.split('\x00'):
                code, path = line[0], line[2:]
                if code == 'C':
                    continue
                statuses[os.path.normpath(path)] = self._status_translate(code)

        return statuses

    def data_status_remote(self):
        if self._remote_url() is None:
            return 'none'

        ahead = behind = True
        try:
            self._run(['outgoing'], catchout=False)
        except VcsError:
            ahead = False

        try:
            self._run(['incoming'], catchout=False)
        except VcsError:
            behind = False

        if ahead:
            return 'diverged' if behind else 'ahead'
        else:
            return 'behind' if behind else 'sync'

    def data_branch(self):
        return self._run(['branch'], catchout=True).rstrip('\n') or None

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
