#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# vcs - a python module to handle various version control systems
# Copyright 2012 Abdó Roig-Maranges <abdo.roig@gmail.com>
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

from .vcs import Vcs, VcsError


class Bzr(Vcs):
    vcsname  = 'bzr'
    HEAD="last:1"

    # Auxiliar stuff
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



    # Repo creation
    #---------------------------

    def init(self):
        """Initializes a repo in current path"""
        self._bzr(self.path, ['init'])
        self.update()


    def clone(self, src):
        """Clones a repo from src"""
        path = os.path.dirname(self.path)
        name = os.path.basename(self.path)
        try:
            os.rmdir(self.path)
        except OSError:
            raise VcsError("Can't clone to %s. It is not an empty directory" % self.path)

        self._bzr(path, ['branch', src, name])
        self.update()



    # Action Interface
    #---------------------------

    def commit(self, message):
        """Commits with a given message"""
        self._bzr(self.path, ['commit', '-m', message])


    def add(self, filelist=None):
        """Adds files to the index, preparing for commit"""
        if filelist != None: self._bzr(self.path, ['add'] + filelist)
        else:                self._bzr(self.path, ['add'])


    def reset(self, filelist=None):
        """Removes files from the index"""
        if filelist != None: self._bzr(self.path, ['remove', '--keep', '--new'] + filelist)
        else:                self._bzr(self.path, ['remove', '--keep', '--new'])


    def pull(self):
        """Pulls a git repo"""
        self._bzr(self.path, ['pull'])


    def push(self):
        """Pushes a git repo"""
        self._bzr(self.path, ['push'])


    def checkout(self, rev):
        """Checks out a branch or revision"""
        self._bzr(self.path, ['update', '-r', rev])


    def extract_file(self, rev, name, dest):
        """Extracts a file from a given revision and stores it in dest dir"""
        if rev == self.INDEX:
            shutil.copyfile(os.path.join(self.path, name), dest)
        else:
            out = self._bzr(self.path, ['cat', '--r', rev, name], catchout=True, bytes=True)
            with open(dest, 'wb') as fd: fd.write(out)



    # Data Interface
    #---------------------------

    def get_status_allfiles(self):
        """Returns a dict indexed by files not in sync their status as values.
           Paths are given relative to the root. Strips trailing '/' from dirs."""
        raw = self._bzr(self.path, ['status', '--short', '--no-classify'], catchout=True, bytes=True)
        L = re.findall('^(..)\s*(.*?)\s*$', raw.decode('utf-8'), re.MULTILINE)
        ret = {}
        for st, p in L:
            sta = self._bzr_file_status(st)
            ret[os.path.normpath(p.strip())] = sta
        return ret


    def get_ignore_allfiles(self):
        """Returns a set of all the ignored files in the repo. Strips trailing '/' from dirs."""
        raw = self._bzr(self.path, ['ls', '--ignored'], catchout=True)
        return set(os.path.normpath(p) for p in raw.split('\n'))


    # TODO: slow due to net access
    def get_remote_status(self):
        """Checks the status of the repo regarding sync state with remote branch"""
        if self.get_remote() == None:
            return "none"

        ahead = behind = True
        try:
            self._bzr(self.path, ['missing', '--mine-only'], silent=True)
        except:
            ahead = False

        try:
            self._bzr(self.path, ['missing', '--theirs-only'], silent=True)
        except:
            behind = False

        if       ahead and     behind: return "diverged"
        elif     ahead and not behind: return "ahead"
        elif not ahead and     behind: return "behind"
        elif not ahead and not behind: return "sync"


    def get_branch(self):
        """Returns the current named branch, if this makes sense for the backend. None otherwise"""
        branch = self._bzr(self.path, ['nick'], catchout=True)
        return branch or None


    def get_log(self, filelist=None, maxres=None):
        """Get the entire log for the current HEAD"""
        if not self._has_head(): return []
        return self._log(refspec=None, filelist=filelist)


    def get_raw_log(self, filelist=None):
        """Gets the raw log as a string"""
        if not self._has_head(): return []
        args = ['log']
        if filelist: args = args + filelist
        return self._bzr(self.path, args, catchout=True)


    def get_raw_diff(self, refspec=None, filelist=None):
        """Gets the raw diff as a string"""
        args = ['diff', '--git']
        if refspec:  args = args + [refspec]
        if filelist: args = args + filelist
        return self._bzr(self.path, args, catchout=True)


    def get_remote(self):
        """Returns the url for the remote repo attached to head"""
        try:
            remote = self._bzr(self.path, ['config', 'parent_location'], catchout=True)
        except VcsError:
            remote = ""

        return remote.strip() or None


    def get_revision_id(self, rev=None):
        """Get a canonical key for the revision rev"""
        if rev == None: rev = self.HEAD
        elif rev == self.INDEX: return None
        rev = self._sanitize_rev(rev)
        try:
            L = self._log(refspec=rev)
        except VcsError:
            L = []
        if len(L) == 0: return None
        else:           return L[0]['revid']


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


    def get_files(self, rev=None):
        """Gets a list of files in revision rev"""
        if rev == None: rev = self.HEAD
        rev = self._sanitize_rev(rev)

        if rev:
            if rev == self.INDEX:  raw = self._bzr(self.path, ["ls"], catchout=True)
            else:                  raw = self._bzr(self.path, ['ls', '--R', '-V', '-r', rev], catchout=True)
            return raw.split('\n')
        else:
            return []

# vim: expandtab:shiftwidth=4:tabstop=4:softtabstop=4:textwidth=80
