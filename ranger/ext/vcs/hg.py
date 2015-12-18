"""Mercurial module"""

import os
import re
from datetime import datetime

from .vcs import Vcs, VcsError

class Hg(Vcs):
    HEAD = 'tip'

    # Generic
    #---------------------------

    def _hg(self, path, args, silent=True, catchout=False, bytes=False):
        return self._vcs(path, 'hg', args, silent=silent, catchout=catchout, bytes=bytes)

    def _has_head(self):
        """Checks whether repo has head"""
        rnum = self._hg(self.path, ['-q', 'identify', '--num', '-r', self.HEAD], catchout=True)
        return rnum != '-1'

    def _sanitize_rev(self, rev):
        if rev == None: return None
        rev = rev.strip()
        if len(rev) == 0: return None
        if rev[-1] == '+': rev = rev[:-1]

        try:
            if int(rev) == 0: return None
        except:
            pass

        return rev

    def _log(self, refspec=None, maxres=None, filelist=None):

        fmt = "changeset: {rev}:{node}\ntag: {tags}\nuser: {author}\ndate: {date}\nsummary: {desc}\n"
        args = ['log', '--template', fmt]

        if refspec:  args = args + ['--limit', '1', '-r', refspec]
        elif maxres: args = args + ['--limit', str(maxres)]

        if filelist: args = args + filelist

        raw = self._hg(self.path, args, catchout=True)
        L = re.findall('^changeset:\s*([0-9]*):([0-9a-zA-Z]*)\s*$\s*^tag:\s*(.*)\s*$\s*^user:\s*(.*)\s*$\s*^date:\s*(.*)$\s*^summary:\s*(.*)\s*$', raw, re.MULTILINE)

        log = []
        for t in L:
            dt = {}
            dt['short'] = t[0].strip()
            dt['revid'] = self._sanitize_rev(t[1].strip())
            dt['author'] = t[3].strip()
            m = re.match('\d+(\.\d+)?', t[4].strip())
            dt['date'] = datetime.fromtimestamp(float(m.group(0)))
            dt['summary'] = t[5].strip()
            log.append(dt)
        return log

    def _hg_file_status(self, st):
        if len(st) != 1: raise VcsError("Wrong hg file status string: %s" % st)
        if   st in "ARM":    return 'staged'
        elif st in "!":      return 'deleted'
        elif st in "I":      return 'ignored'
        elif st in "?":      return 'untracked'
        elif st in "X":      return 'conflict'
        elif st in "C":      return 'sync'
        else:                return 'unknown'

    # Action Interface
    #---------------------------

    def add(self, filelist=None):
        """Adds files to the index, preparing for commit"""
        if filelist != None: self._hg(self.path, ['addremove'] + filelist)
        else:                self._hg(self.path, ['addremove'])

    def reset(self, filelist=None):
        """Removes files from the index"""
        if filelist == None: filelist = self.get_status_subpaths().keys()
        self._hg(self.path, ['forget'] + filelist)

    # Data Interface
    #---------------------------

    def get_status_subpaths(self):
        """Returns a dict indexed by files not in sync their status as values.
           Paths are given relative to the root. Strips trailing '/' from dirs."""
        raw = self._hg(self.path, ['status'], catchout=True, bytes=True)
        L = re.findall('^(.)\s*(.*?)\s*$', raw.decode('utf-8'), re.MULTILINE)
        ret = {}
        for st, p in L:
            # Detect conflict by the existence of .orig files
            if st == '?' and re.match('^.*\.orig\s*$', p):  st = 'X'
            sta = self._hg_file_status(st)
            ret[os.path.normpath(p.strip())] = sta
        return ret

    def get_status_remote(self):
        """Checks the status of the repo regarding sync state with remote branch"""
        if self.get_remote() == None:
            return "none"

        ahead = behind = True
        try:
            self._hg(self.path, ['outgoing'], silent=True)
        except:
            ahead = False

        try:
            self._hg(self.path, ['incoming'], silent=True)
        except:
            behind = False

        if       ahead and     behind: return "diverged"
        elif     ahead and not behind: return "ahead"
        elif not ahead and     behind: return "behind"
        elif not ahead and not behind: return "sync"

    def get_branch(self):
        """Returns the current named branch, if this makes sense for the backend. None otherwise"""
        branch = self._hg(self.path, ['branch'], catchout=True)
        return branch or None

    def get_info(self, rev=None):
        """Gets info about the given revision rev"""
        if rev == None: rev = self.HEAD
        rev = self._sanitize_rev(rev)
        if rev == self.HEAD and not self._has_head(): return None

        L = self._log(refspec=rev)
        if len(L) == 0:
            raise VcsError("Revision %s does not exist" % rev)
        elif len(L) > 1:
            raise VcsError("More than one instance of revision %s ?!?" % rev)
        else:
            return L[0]
