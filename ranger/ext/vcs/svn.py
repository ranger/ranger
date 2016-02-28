# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""Subversion module"""

from datetime import datetime
import os
from xml.etree import ElementTree as etree

from .vcs import Vcs, VcsError


class SVN(Vcs):
    """VCS implementation for Subversion"""
    # Generic
    _status_translations = (
        ('ADR', 'staged'),
        ('C', 'conflict'),
        ('I', 'ignored'),
        ('M~', 'changed'),
        ('X', 'none'),
        ('?', 'untracked'),
        ('!', 'deleted'),
    )

    def _log(self, refspec=None, maxres=None, filelist=None):
        """Retrieves log message and parses it"""
        args = ['log', '--xml']

        if refspec:
            args += ['--limit', '1', '--revision', refspec]
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
        for entry in etree.fromstring(output).findall('./logentry'):
            new = {}
            new['short'] = entry.get('revision')
            new['revid'] = entry.get('revision')
            new['author'] = entry.find('./author').text
            new['date'] = datetime.strptime(
                entry.find('./date').text,
                '%Y-%m-%dT%H:%M:%S.%fZ',
            )
            new['summary'] = entry.find('./msg').text.split('\n')[0]
            log.append(new)
        return log

    def _status_translate(self, code):
        """Translate status code"""
        for code_x, status in self._status_translations:
            if code in code_x:
                return status
        return 'unknown'

    def _remote_url(self):
        """Remote url"""
        try:
            output = self._run(['info', '--xml']).rstrip('\n')
        except VcsError:
            return None
        if not output:
            return None
        return etree.fromstring(output).find('./entry/url').text or None

    # Action Interface

    def action_add(self, filelist=None):
        args = ['add']
        if filelist:
            args += ['--'] + filelist
        self._run(args, catchout=False)

    def action_reset(self, filelist=None):
        args = ['revert', '--']
        if filelist:
            args += filelist
        else:
            args += self.rootvcs.status_subpaths.keys()
        self._run(args, catchout=False)

    # Data Interface

    def data_status_root(self):
        statuses = set()

        # Paths with status
        output = self._run(['status']).rstrip('\n')
        if not output:
            return 'sync'
        for line in output.split('\n'):
            code = line[0]
            if code == ' ':
                continue
            statuses.add(self._status_translate(code))

        for status in self.DIRSTATUSES:
            if status in statuses:
                return status
        return 'sync'

    def data_status_subpaths(self):
        statuses = {}

        # Paths with status
        output = self._run(['status']).rstrip('\n')
        if output:
            for line in output.split('\n'):
                code, path = line[0], line[8:]
                if code == ' ':
                    continue
                statuses[os.path.normpath(path)] = self._status_translate(code)

        return statuses

    def data_status_remote(self):
        remote = self._remote_url()
        if remote is None or remote.startswith('file://'):
            return 'none'
        return 'unknown'

    def data_branch(self):
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
            raise VcsError('More than one instance of revision {0:s}'.format(rev))
