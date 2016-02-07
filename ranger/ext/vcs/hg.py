# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""Mercurial module"""

import os
import re
from datetime import datetime

from .vcs import Vcs, VcsError

class Hg(Vcs):
    """VCS implementation for Mercurial"""
    HEAD = 'tip'

    # Generic
    #---------------------------

    def _hg(self, path, args, silent=True, catchout=False, retbytes=False):
        return self._vcs(path, 'hg', args, silent=silent, catchout=catchout, retbytes=retbytes)

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

    def action_add(self, filelist=None):
        if filelist != None: self._hg(self.path, ['addremove'] + filelist)
        else:                self._hg(self.path, ['addremove'])

    def action_reset(self, filelist=None):
        if filelist == None: filelist = self.data_status_subpaths().keys()
        self._hg(self.path, ['forget'] + filelist)

    # Data Interface
    #---------------------------

    def data_status_subpaths(self):
        raw = self._hg(self.path, ['status'], catchout=True, retbytes=True)
        L = re.findall('^(.)\s*(.*?)\s*$', raw.decode('utf-8'), re.MULTILINE)
        ret = {}
        for st, p in L:
            # Detect conflict by the existence of .orig files
            if st == '?' and re.match('^.*\.orig\s*$', p):  st = 'X'
            sta = self._hg_file_status(st)
            ret[os.path.normpath(p.strip())] = sta
        return ret

    def data_status_remote(self):
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

    def data_branch(self):
        branch = self._hg(self.path, ['branch'], catchout=True)
        return branch or None

    def data_info(self, rev=None):
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
