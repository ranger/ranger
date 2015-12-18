# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""Subversion module"""

from __future__ import with_statement
import os
import re
import logging
from datetime import datetime
from .vcs import Vcs, VcsError

class SVN(Vcs):
    """VCS implementation for Subversion"""
    HEAD = 'HEAD'

    # Generic
    #---------------------------

    def _svn(self, path, args, silent=True, catchout=False, retbytes=False):
        return self._vcs(path, 'svn', args, silent=silent, catchout=catchout, retbytes=retbytes)

    def _has_head(self):
        """Checks whether repo has head"""
        return True

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
        """ Retrieves log message and parses it.
        """
        args = ['log']

        if refspec:  args = args + ['--limit', '1', '-r', refspec]
        elif maxres: args = args + ['--limit', str(maxres)]

        if filelist: args = args + filelist
        logging.debug('Running svn log')
        logging.debug(args)

        raw = self._svn(self.path, args, catchout=True)
        logging.debug(raw)
        L = re.findall(r"""^[-]*\s*            # Dash line
                       r([0-9]*)\s\|\s         # Revision          [0]
                       (.*)\s\|\s              # Author            [1]
                       (.*?)\s                 # Date              [2]
                       (.*?)\s                 # Time              [3]
                       .*?\|\s*?               # Dump rest of date string
                       ([0-9])+\sline(?:s)?\s* # Number of line(s) [4]
                       (.*)\s                  # Log Message       [5]
                       [-]+\s*                 # Dash line
                       $""", raw, re.MULTILINE | re.VERBOSE)

        log = []
        for t in L:
            logging.debug(t)
            dt = {}
            dt['short'] = t[0].strip()
            dt['revid'] = t[0].strip()
            dt['author'] = t[1].strip()
            dt['date'] = datetime.strptime(t[2]+'T'+t[3], "%Y-%m-%dT%H:%M:%S")
            dt['summary'] = t[5].strip()
            log.append(dt)
            logging.debug(log)
        return log

    def _svn_file_status(self, st):
        if len(st) != 1: raise VcsError("Wrong hg file status string: %s" % st)
        if   st in "A":  return 'staged'
        elif st in "D":  return 'deleted'
        elif st in "I":  return 'ignored'
        elif st in "?":  return 'untracked'
        elif st in "C":  return 'conflict'
        else:            return 'unknown'

    # Action Interface
    #---------------------------

    def action_add(self, filelist=None):
        """Adds files to the index, preparing for commit"""
        if filelist != None: self._svn(self.path, ['add'] + filelist)
        else:                self._svn(self.path, ['add'])

    def action_reset(self, filelist=None):
        """Equivalent to svn revert"""
        if filelist == None: filelist = self.data_status_subpaths().keys()
        self._svn(self.path, ['revert'] + filelist)

    # Data Interface
    #---------------------------

    def data_status_subpaths(self):
        """Returns a dict indexed by files not in sync their status as values.
           Paths are given relative to the root. Strips trailing '/' from dirs."""
        raw = self._svn(self.path, ['status'], catchout=True, retbytes=True)
#        logging.debug(raw)
        L = re.findall(r'^(.)\s*(.*?)\s*$', raw.decode('utf-8'), re.MULTILINE)
        ret = {}
        for st, p in L:
            # Detect conflict by the existence of .orig files
            if st == '?' and re.match(r'^.*\.orig\s*$', p): st = 'X'
            sta = self._svn_file_status(st)
            ret[os.path.normpath(p.strip())] = sta
        return ret

    def data_status_remote(self):
        """Checks the status of the repo regarding sync state with remote branch.

        I'm not sure this make sense for SVN so we're just going to return 'sync'"""
        return 'sync'

    def data_branch(self):
        """Returns the current named branch, if this makes sense for the backend. None otherwise"""
        return None
        branch = self._svn(self.path, ['branch'], catchout=True)
        return branch or None

    def data_info(self, rev=None):
        """Gets info about the given revision rev"""
        if rev == None: rev = self.HEAD
        rev = self._sanitize_rev(rev)
        if rev == self.HEAD and not self._has_head(): return None
        logging.debug('refspec is ' + str(rev))
        L = self._log(refspec=rev)
        logging.debug(len(L))
        if len(L) == 0:
            raise VcsError("Revision %s does not exist" % rev)
        elif len(L) > 1:
            raise VcsError("More than one instance of revision %s ?!?" % rev)
        else:
            return L[0]
