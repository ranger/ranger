# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""GNU Bazaar module"""

from __future__ import (absolute_import, print_function)

from datetime import datetime
import os
import re

from .vcs import Vcs, VcsError


class Bzr(Vcs):
    """VCS implementation for GNU Bazaar"""
    HEAD = 'last:1'

    _status_translations = (
        ('+ -R', 'K NM', 'staged'),
        (' -', 'D', 'deleted'),
        ('?', ' ', 'untracked'),
    )

    # Generic

    def _remote_url(self):
        """Remote url"""
        try:
            return self._run(['config', 'parent_location']) or None
        except VcsError:
            return None

    def _log(self, refspec=None, filelist=None):
        """Returns an array of dicts containing revision info for refspec"""
        args = ['log', '--log-format', 'long', '--levels', '0', '--show-ids']
        if refspec:
            args += ['--revision', refspec]
        if filelist:
            args += ['--'] + filelist

        try:
            output = self._run(args)
        except VcsError:
            return None
        # pylint: disable=no-member
        entries = re.findall(r'-+\n(.+?)\n(?:-|\Z)', output, re.MULTILINE | re.DOTALL)
        # pylint: enable=no-member

        log = []
        for entry in entries:
            new = {}
            try:
                new['short'] = re.search(r'^revno: ([0-9]+)', entry, re.MULTILINE).group(1)
                new['revid'] = re.search(r'^revision-id: (.+)$', entry, re.MULTILINE).group(1)
                new['author'] = re.search(r'^committer: (.+)$', entry, re.MULTILINE).group(1)
                new['date'] = datetime.strptime(
                    re.search(r'^timestamp: (.+)$', entry, re.MULTILINE).group(1),
                    '%a %Y-%m-%d %H:%M:%S %z'
                )
                new['summary'] = re.search(r'^message:\n  (.+)$', entry, re.MULTILINE).group(1)
            except AttributeError:
                return None
            log.append(new)
        return log

    def _status_translate(self, code):
        """Translate status code"""
        for code_x, code_y, status in self._status_translations:
            if code[0] in code_x and code[1] in code_y:
                return status
        return 'unknown'

    # Action Interface

    def action_add(self, filelist=None):
        args = ['add']
        if filelist:
            args += ['--'] + filelist
        self._run(args, catchout=False)

    def action_reset(self, filelist=None):
        args = ['remove', '--keep', '--new']
        if filelist:
            args += ['--'] + filelist
        self._run(args, catchout=False)

    # Data Interface

    def data_status_root(self):
        statuses = set()

        # Paths with status
        lines = self._run(['status', '--short', '--no-classify']).split('\n')
        if not lines:
            return 'sync'
        for line in lines:
            statuses.add(self._status_translate(line[:2]))

        for status in self.DIRSTATUSES:
            if status in statuses:
                return status

        return 'sync'

    def data_status_subpaths(self):
        statuses = {}

        # Ignored
        paths = self._run(['ls', '--null', '--ignored']).split('\0')[:-1]
        for path in paths:
            statuses[path] = 'ignored'

        # Paths with status
        lines = self._run(['status', '--short', '--no-classify']).split('\n')
        for line in lines:
            statuses[os.path.normpath(line[4:])] = self._status_translate(line[:2])

        return statuses

    def data_status_remote(self):
        if not self._remote_url():
            return 'none'
        return 'unknown'

    def data_branch(self):
        try:
            return self._run(['nick']) or None
        except VcsError:
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
