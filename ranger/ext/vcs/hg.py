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

        args = ['log', '--template', 'json']
        if refspec:
            args += ['--limit', '1', '--rev', refspec]
        elif maxres:
            args += ['--limit', str(maxres)]
        if filelist:
            args += ['--'] + filelist

        try:
            output = self._run(args)
        except VcsError:
            return None
        if not output:
            return None

        log = []
        for entry in json.loads(output):
            new = {}
            new['short'] = entry['rev']
            new['revid'] = entry['node']
            new['author'] = entry['user']
            new['date'] = datetime.fromtimestamp(entry['date'][0])
            new['summary'] = entry['desc']
            log.append(new)
        return log

    def _remote_url(self):
        """Remote url"""
        try:
            return self._run(['showconfig', 'paths.default']) or None
        except VcsError:
            return None

    def _status_translate(self, code):
        """Translate status code"""
        for code_x, status in self._status_translations:
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
            args += self.rootvcs.status_subpaths.keys()  # pylint: disable=no-member
        self._run(args, catchout=False)

    # Data interface

    def data_status_root(self):
        statuses = set()

        # Paths with status
        for entry in json.loads(self._run(['status', '--all', '--template', 'json'])):
            if entry['status'] == 'C':
                continue
            statuses.add(self._status_translate(entry['status']))

        if statuses:
            for status in self.DIRSTATUSES:
                if status in statuses:
                    return status
        return 'sync'

    def data_status_subpaths(self):
        statuses = {}

        # Paths with status
        for entry in json.loads(self._run(['status', '--all', '--template', 'json'])):
            if entry['status'] == 'C':
                continue
            statuses[os.path.normpath(entry['path'])] = self._status_translate(entry['status'])

        return statuses

    def data_status_remote(self):
        if self._remote_url() is None:
            return 'none'
        return 'unknown'

    def data_branch(self):
        return self._run(['branch']) or None

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
