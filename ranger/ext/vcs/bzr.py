# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""GNU Bazaar module"""

import os
import re
from datetime import datetime
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
    #---------------------------

    def _bzr(self, args, path=None, catchout=True, retbytes=False):
        """Run a bzr command"""
        return self._vcs(['bzr'] + args, path or self.path, catchout=catchout, retbytes=retbytes)

    def _remote_url(self):
        """Returns remote url"""
        try:
            return self._bzr(['config', 'parent_location']).rstrip() or None
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
            output = self._bzr(args)
        except VcsError:
            return None
        entries = re.findall(r'-+\n(.+?)\n(?:-|\Z)', output, re.MULTILINE | re.DOTALL)

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

    def _bzr_status_translate(self, code):
        """Translate status code"""
        for X, Y, status in self._status_translations:
            if code[0] in X and code[1] in Y:
                return status
        return 'unknown'

    # Action Interface
    #---------------------------

    def action_add(self, filelist=None):
        args = ['add']
        if filelist:
            args += ['--'] + filelist
        self._bzr(args, catchout=False)

    def action_reset(self, filelist=None):
        args = ['remove', '--keep', '--new']
        if filelist:
            args += ['--'] + filelist
        self._bzr(args, catchout=False)

    # Data Interface
    #---------------------------

    def data_status_root(self):
        statuses = set()

        # Paths with status
        for line in self._bzr(['status', '--short', '--no-classify']).splitlines():
            statuses.add(self._bzr_status_translate(line[:2]))

        for status in self.DIRSTATUSES:
            if status in statuses:
                return status
        return 'sync'

    def data_status_subpaths(self):
        statuses = {}

        # Ignored
        for path in self._bzr(['ls', '--null', '--ignored']).split('\x00')[:-1]:
            statuses[path] = 'ignored'

        # Paths with status
        for line in self._bzr(['status', '--short', '--no-classify']).splitlines():
            statuses[os.path.normpath(line[4:])] = self._bzr_status_translate(line[:2])

        return statuses

    def data_status_remote(self):
        if not self._remote_url():
            return 'none'

        return 'unknown'

    def data_branch(self):
        try:
            return self._bzr(['nick']).rstrip() or None
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
            raise VcsError('More than one instance of revision {0:s} ?!?'.format(rev))
