"""GNU Bazaar module"""

import os
import re
from datetime import datetime

from .vcs import Vcs, VcsError

class Bzr(Vcs):
    """VCS implementiation for Bzr"""
    HEAD="last:1"

    # Generic
    #---------------------------

    def _bzr(self, path, args, silent=True, catchout=False, bytes=False):
        return self._vcs(path, 'bzr', args, silent=silent, catchout=catchout, bytes=bytes)

    def _has_head(self):
        """Checks whether repo has head"""
        rnum = self._bzr(self.path, ['revno'], catchout=True)
        return rnum != '0'

    def _sanitize_rev(self, rev):
        if rev == None: return None
        rev = rev.strip()
        if len(rev) == 0: return None

        return rev

    def _log(self, refspec=None, filelist=None):
        """Gets a list of dicts containing revision info, for the revisions matching refspec"""
        args = ['log', '-n0', '--show-ids']
        if refspec: args = args + ["-r", refspec]

        if filelist: args = args + filelist

        raw = self._bzr(self.path, args, catchout=True, silent=True)
        L = re.findall('-+$(.*?)^-', raw + '\n---', re.MULTILINE | re.DOTALL)

        log = []
        for t in L:
            t = t.strip()
            if len(t) == 0: continue

            dt = {}
            m = re.search('^revno:\s*([0-9]+)\s*$', t, re.MULTILINE)
            if m: dt['short'] = m.group(1).strip()
            m = re.search('^revision-id:\s*(.+)\s*$', t, re.MULTILINE)
            if m: dt['revid'] = m.group(1).strip()
            m = re.search('^committer:\s*(.+)\s*$', t, re.MULTILINE)
            if m: dt['author'] = m.group(1).strip()
            m = re.search('^timestamp:\s*(.+)\s*$', t, re.MULTILINE)
            if m: dt['date'] = datetime.strptime(m.group(1).strip(), '%a %Y-%m-%d %H:%M:%S %z')
            m = re.search('^message:\s*^(.+)$', t, re.MULTILINE)
            if m: dt['summary'] = m.group(1).strip()
            log.append(dt)
        return log

    def _bzr_file_status(self, st):
        st = st.strip()
        if   st in "AM":     return 'staged'
        elif st in "D":      return 'deleted'
        elif st in "?":      return 'untracked'
        else:                return 'unknown'

    # Action Interface
    #---------------------------

    def add(self, filelist=None):
        """Adds files to the index, preparing for commit"""
        if filelist != None: self._bzr(self.path, ['add'] + filelist)
        else:                self._bzr(self.path, ['add'])

    def reset(self, filelist=None):
        """Removes files from the index"""
        if filelist != None: self._bzr(self.path, ['remove', '--keep', '--new'] + filelist)
        else:                self._bzr(self.path, ['remove', '--keep', '--new'])

    # Data Interface
    #---------------------------

    def get_status_subpaths(self):
        """Returns a dict indexed by files not in sync their status as values.
           Paths are given relative to the root. Strips trailing '/' from dirs."""
        raw = self._bzr(self.path, ['status', '--short', '--no-classify'], catchout=True, bytes=True)
        L = re.findall('^(..)\s*(.*?)\s*$', raw.decode('utf-8'), re.MULTILINE)
        ret = {}
        for st, p in L:
            sta = self._bzr_file_status(st)
            ret[os.path.normpath(p.strip())] = sta
        return ret

    def get_status_remote(self):
        """Returns the url for the remote repo attached to head"""
        try:
            remote = self._bzr(self.path, ['config', 'parent_location'], catchout=True)
        except VcsError:
            remote = ""

        return remote.strip() or None

    def get_branch(self):
        """Returns the current named branch, if this makes sense for the backend. None otherwise"""
        branch = self._bzr(self.path, ['nick'], catchout=True)
        return branch or None

    def get_info(self, rev=None):
        """Gets info about the given revision rev"""
        if rev == None: rev = self.HEAD
        rev = self._sanitize_rev(rev)
        if rev == self.HEAD and not self._has_head(): return []

        L = self._log(refspec=rev)
        if len(L) == 0:
            raise VcsError("Revision %s does not exist" % rev)
        elif len(L) > 1:
            raise VcsError("More than one instance of revision %s ?!?" % rev)
        else:
            return L[0]
