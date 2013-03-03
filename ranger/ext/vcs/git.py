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

from .vcs import Vcs, VcsError


class Git(Vcs):
    vcsname  = 'git'

    # Auxiliar stuff
    #---------------------------

    def _git(self, path, args, silent=True, catchout=False, bytes=False):
        return self._vcs(path, 'git', args, silent=silent, catchout=catchout, bytes=bytes)


    def _has_head(self):
        """Checks whether repo has head"""
        try:
            self._git(self.path, ['rev-parse', 'HEAD'], silent=True)
        except VcsError:
            return False
        return True


    def _head_ref(self):
        """Gets HEAD's ref"""
        ref = self._git(self.path, ['symbolic-ref', self.HEAD], catchout=True, silent=True)
        return ref.strip() or None


    def _remote_ref(self, ref):
        """Gets remote ref associated to given ref"""
        if ref == None: return None
        remote = self._git(self.path, ['for-each-ref', '--format=%(upstream)', ref], catchout=True, silent=True)
        return remote.strip() or None


    def _sanitize_rev(self, rev):
        if rev == None: return None
        return rev.strip()


    def _log(self, refspec=None, maxres=None, filelist=None):
        """Gets a list of dicts containing revision info, for the revisions matching refspec"""
        fmt = '--pretty=%h %H%nAuthor: %an <%ae>%nDate: %ct%nSubject: %s%n'

        args = ['--no-pager', 'log', fmt]
        if refspec:  args = args + ['-1', refspec]
        elif maxres: args = args + ['-%d' % maxres]

        if filelist: args = args + ['--'] + filelist

        raw = self._git(self.path, args, catchout=True)
        L = re.findall('^\s*(\w*)\s*(\w*)\s*^Author:\s*(.*)\s*^Date:\s*(.*)\s*^Subject:\s*(.*)\s*', raw, re.MULTILINE)

        log = []
        for t in L:
            dt = {}
            dt['short'] = t[0].strip()
            dt['revid'] = t[1].strip()
            dt['author'] = t[2].strip()
            m = re.match('\d+(\.\d+)?', t[3].strip())
            dt['date'] = datetime.fromtimestamp(float(m.group(0)))
            dt['summary'] = t[4].strip()
            log.append(dt)
        return log


    def _git_file_status(self, st):
        if len(st) != 2: raise VcsError("Wrong git file status string: %s" % st)
        X, Y = (st[0], st[1])
        if   X in " "      and Y in " " : return 'sync'
        elif X in "MADRC"  and Y in " " : return 'staged'
        elif X in "MADRC " and Y in "M":  return 'changed'
        elif X in "MARC "  and Y in "D":  return 'deleted'
        elif X in "U" or Y in "U":        return 'conflict'
        elif X in "A" and Y in "A":       return 'conflict'
        elif X in "D" and Y in "D":       return 'conflict'
        elif X in "?" and Y in "?":       return 'untracked'
        elif X in "!" and Y in "!":       return 'ignored'
        else:                             return 'unknown'



    # Repo creation
    #---------------------------

    def init(self):
        """Initializes a repo in current path"""
        self._git(self.path, ['init'])
        self.update()


    def clone(self, src):
        """Clones a repo from src"""
        name = os.path.basename(self.path)
        path = os.path.dirname(self.path)
        try:
            os.rmdir(self.path)
        except OSError:
            raise VcsError("Can't clone to %s. It is not an empty directory" % self.path)

        self._git(path, ['clone', src, name])
        self.update()



    # Action interface
    #---------------------------

    def commit(self, message):
        """Commits with a given message"""
        self._git(self.path, ['commit', '-m', message])


    def add(self, filelist=None):
        """Adds files to the index, preparing for commit"""
        if filelist != None: self._git(self.path, ['add', '-A'] + filelist)
        else:                self._git(self.path, ['add', '-A'])


    def reset(self, filelist=None):
        """Removes files from the index"""
        if filelist != None: self._git(self.path, ['reset'] + filelist)
        else:                self._git(self.path, ['reset'])


    def pull(self, br=None):
        """Pulls from remote"""
        if br: self._git(self.path, ['pull', br])
        else:  self._git(self.path, ['pull'])


    def push(self, br=None):
        """Pushes to remote"""
        if br: self._git(self.path, ['push', br])
        else:  self._git(self.path, ['push'])


    def checkout(self, rev):
        """Checks out a branch or revision"""
        self._git(self.path, ['checkout', self._sanitize_rev(rev)])


    def extract_file(self, rev, name, dest):
        """Extracts a file from a given revision and stores it in dest dir"""
        if rev == self.INDEX:
            shutil.copyfile(os.path.join(self.path, name), dest)
        else:
            out = self._git(self.path, ['--no-pager', 'show', '%s:%s' % (self._sanitize_rev(rev), name)],
                            catchout=True, bytes=True)
            with open(dest, 'wb') as fd: fd.write(out)



    # Data Interface
    #---------------------------

    def get_status_allfiles(self):
        """Returns a dict indexed by files not in sync their status as values.
           Paths are given relative to the root. Strips trailing '/' from dirs."""
        raw = self._git(self.path, ['status', '--porcelain'], catchout=True, bytes=True)
        L = re.findall('^(..)\s*(.*?)\s*$', raw.decode('utf-8'), re.MULTILINE)
        ret = {}
        for st, p in L:
            sta = self._git_file_status(st)
            if 'R' in st:
                m = re.match('^(.*)\->(.*)$', p)
                if m: p = m.group(2).strip()
            ret[os.path.normpath(p.strip())] = sta
        return ret


    def get_ignore_allfiles(self):
        """Returns a set of all the ignored files in the repo. Strips trailing '/' from dirs."""
        raw = self._git(self.path, ['ls-files', '--others', '--directory', '-i', '--exclude-standard'],
                        catchout=True)
        return set(os.path.normpath(p) for p in raw.split('\n'))


    def get_remote_status(self):
        """Checks the status of the repo regarding sync state with remote branch"""
        try:
            head = self._head_ref()
            remote = self._remote_ref(head)
        except VcsError:
            head = remote = None

        if head and remote:
            raw = self._git(self.path, ['rev-list', '--left-right', '%s...%s' % (remote, head)], catchout=True)
            ahead  = re.search("^>", raw, flags=re.MULTILINE)
            behind = re.search("^<", raw, flags=re.MULTILINE)

            if       ahead and     behind: return "diverged"
            elif     ahead and not behind: return "ahead"
            elif not ahead and     behind: return "behind"
            elif not ahead and not behind: return "sync"
        else:                            return "none"


    def get_branch(self):
        """Returns the current named branch, if this makes sense for the backend. None otherwise"""
        try:
            head = self._head_ref()
        except VcsError:
            head = None

        if head:
            m = re.match('refs/heads/([^/]*)', head)
            if m: return m.group(1).strip()
        else:
            return "detached"

        return None


    def get_log(self, filelist=None, maxres=None):
        """Get the entire log for the current HEAD"""
        if not self._has_head(): return []
        return self._log(refspec=None, maxres=maxres, filelist=filelist)


    def get_raw_log(self, filelist=None):
        """Gets the raw log as a string"""
        if not self._has_head(): return []
        args = ['log']
        if filelist: args = args + ['--'] + filelist
        return self._git(self.path, args, catchout=True)


    def get_raw_diff(self, refspec=None, filelist=None):
        """Gets the raw diff as a string"""
        args = ['diff']
        if refspec:  args = args + [refspec]
        if filelist: args = args + ['--'] + filelist
        return self._git(self.path, args, catchout=True)


    def get_remote(self):
        """Returns the url for the remote repo attached to head"""
        if self.is_repo():
            try:
                ref = self._head_ref()
                remote = self._remote_ref(ref)
            except VcsError:
                ref = remote = None

            if remote:
                m = re.match('refs/remotes/([^/]*)/', remote)
                if m:
                    url = self._git(self.path, ['config', '--get', 'remote.%s.url' % m.group(1)], catchout=True)
                    return url.strip() or None
        return None


    def get_revision_id(self, rev=None):
        """Get a canonical key for the revision rev"""
        if rev == None: rev = self.HEAD
        elif rev == self.INDEX: return None
        rev = self._sanitize_rev(rev)

        return self._sanitize_rev(self._git(self.path, ['rev-parse', rev], catchout=True))


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
            if rev == self.INDEX:  raw = self._git(self.path, ["ls-files"], catchout=True)
            else:                  raw = self._git(self.path, ['ls-tree', '--name-only', '-r', rev], catchout=True)
            return raw.split('\n')
        else:
            return []

# vim: expandtab:shiftwidth=4:tabstop=4:softtabstop=4:textwidth=80
