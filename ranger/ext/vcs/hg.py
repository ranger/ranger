#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# vcs - a python module to handle various version control systems
# Copyright 2011, 2012 Abdó Roig-Maranges <abdo.roig@gmail.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import shutil
from datetime import datetime
try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser

from .vcs import Vcs, VcsError


class Hg(Vcs):
    vcsname  = 'hg'
    HEAD = 'tip'
    # Auxiliar stuff
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



    # Repo creation
    #---------------------------

    def init(self):
        """Initializes a repo in current path"""
        self._hg(self.path, ['init'])
        self.update()


    def clone(self, src):
        """Clones a repo from src"""
        name = os.path.basename(self.path)
        path = os.path.dirname(self.path)
        try:
            os.rmdir(self.path)
        except OSError:
            raise VcsError("Can't clone to %s. It is not an empty directory" % self.path)

        self._hg(path, ['clone', src, name])
        self.update()



    # Action Interface
    #---------------------------

    def commit(self, message):
        """Commits with a given message"""
        self._hg(self.path, ['commit', '-m', message])


    def add(self, filelist=None):
        """Adds files to the index, preparing for commit"""
        if filelist != None: self._hg(self.path, ['addremove'] + filelist)
        else:                self._hg(self.path, ['addremove'])


    def reset(self, filelist=None):
        """Removes files from the index"""
        if filelist == None: filelist = self.get_status_allfiles().keys()
        self._hg(self.path, ['forget'] + filelist)


    def pull(self):
        """Pulls a hg repo"""
        self._hg(self.path, ['pull', '-u'])


    def push(self):
        """Pushes a hg repo"""
        self._hg(self.path, ['push'])


    def checkout(self, rev):
        """Checks out a branch or revision"""
        self._hg(self.path, ['update', rev])


    def extract_file(self, rev, name, dest):
        """Extracts a file from a given revision and stores it in dest dir"""
        if rev == self.INDEX:
            shutil.copyfile(os.path.join(self.path, name), dest)
        else:
            self._hg(self.path, ['cat', '--rev', rev, '--output', dest, name])


    # Data Interface
    #---------------------------

    def get_status_allfiles(self):
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


    def get_ignore_allfiles(self):
        """Returns a set of all the ignored files in the repo"""
        raw = self._hg(self.path, ['status', '-i'], catchout=True, bytes=True)
        L = re.findall('^I\s*(.*?)\s*$', raw.decode('utf-8'), re.MULTILINE)
        return set(L)


    def get_remote_status(self):
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


    def get_log(self, filelist=None, maxres=None):
        """Get the entire log for the current HEAD"""
        if not self._has_head(): return []
        return self._log(refspec=None, maxres=maxres, filelist=filelist)


    def get_raw_log(self, filelist=None):
        """Gets the raw log as a string"""
        if not self._has_head(): return []
        args = ['log']
        if filelist: args = args + filelist
        return self._hg(self.path, args, catchout=True)


    def get_raw_diff(self, refspec=None, filelist=None):
        """Gets the raw diff as a string"""
        args = ['diff', '--git']
        if refspec:  args = args + [refspec]
        if filelist: args = args + filelist
        return self._hg(self.path, args, catchout=True)


    def get_remote(self, rev=None):
        """Returns the url for the remote repo attached to head"""
        remote = self._hg(self.path, ['showconfig', 'paths.default'], catchout=True)
        return remote or None


    def get_revision_id(self, rev=None):
        """Get a canonical key for the revision rev"""
        if rev == None: rev = self.HEAD
        elif rev == self.INDEX: return None
        rev = self._sanitize_rev(rev)

        return self._sanitize_rev(self._hg(self.path, ['-q', 'identify', '--id', '-r', rev], catchout=True))


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


    def get_files(self, rev=None):
        """Gets a list of files in revision rev"""
        if rev == None: rev = self.HEAD
        rev = self._sanitize_rev(rev)

        if rev:
            if rev == self.INDEX: raw = self._hg(self.path, ['locate', "*"], catchout=True)
            else:                 raw = self._hg(self.path, ['locate', '--rev', rev, "*"], catchout=True)
            return raw.split('\n')
        else:
            return []


# vim: expandtab:shiftwidth=4:tabstop=4:softtabstop=4:textwidth=80
