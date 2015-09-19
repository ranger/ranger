# -*- coding: utf-8 -*-
# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# Author: Abdó Roig-Maranges <abdo.roig@gmail.com>, 2011-2012
#         Ryan Burns <rdburns@gmail.com>, 2015
#
# R. Burns start with Abdó's Hg module and modified it for Subversion.
#
# vcs - a python module to handle various version control systems

from __future__ import with_statement
import os
import re
import shutil
import logging
from datetime import datetime
from .vcs import Vcs, VcsError

#logging.basicConfig(filename='rangersvn.log',level=logging.DEBUG,
#                    filemode='w')

class SVN(Vcs):
    vcsname = 'svn'
    HEAD = 'HEAD'
    # Auxiliar stuff
    #---------------------------

    def _svn(self, path, args, silent=True, catchout=False, bytes=False):
        return self._vcs(path, 'svn', args, silent=silent, catchout=catchout, bytes=bytes)


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



    # Repo creation
    #---------------------------

    def init(self):
        """Initializes a repo in current path"""
        self._svn(self.path, ['init'])
        self.update()


    def clone(self, src):
        """Checks out SVN repo"""
        name = os.path.basename(self.path)
        path = os.path.dirname(self.path)
        try:
            os.rmdir(self.path)
        except OSError:
            raise VcsError("Can't clone to %s. It is not an empty directory" % self.path)

        self._svn(path, ['co', src, name])
        self.update()



    # Action Interface
    #---------------------------

    def commit(self, message):
        """Commits with a given message"""
        self._svn(self.path, ['commit', '-m', message])


    def add(self, filelist=None):
        """Adds files to the index, preparing for commit"""
        if filelist != None: self._svn(self.path, ['add'] + filelist)
        else:                self._svn(self.path, ['add'])


    def reset(self, filelist=None):
        """Equivalent to svn revert"""
        if filelist == None: filelist = self.get_status_allfiles().keys()
        self._svn(self.path, ['revert'] + filelist)


    def pull(self):
        """Executes SVN Update"""
        self._svn(self.path, ['update'])


    def push(self):
        """Push doesn't have an SVN analog."""
        raise NotImplementedError


    def checkout(self, rev):
        """Checks out a branch or revision"""
        raise NotImplementedError
        self._svn(self.path, ['update', rev])


    def extract_file(self, rev, name, dest):
        """Extracts a file from a given revision and stores it in dest dir"""
        if rev == self.INDEX:
            shutil.copyfile(os.path.join(self.path, name), dest)
        else:
            file_contents = self._svn(self.path, ['cat', '-r', rev, name], catchout=True)
            with open(dest, 'w') as f:
                f.write(file_contents)


    # Data Interface
    #---------------------------

    def get_status_allfiles(self):
        """Returns a dict indexed by files not in sync their status as values.
           Paths are given relative to the root. Strips trailing '/' from dirs."""
        raw = self._svn(self.path, ['status'], catchout=True, bytes=True)
#        logging.debug(raw)
        L = re.findall(r'^(.)\s*(.*?)\s*$', raw.decode('utf-8'), re.MULTILINE)
        ret = {}
        for st, p in L:
            # Detect conflict by the existence of .orig files
            if st == '?' and re.match(r'^.*\.orig\s*$', p): st = 'X'
            sta = self._svn_file_status(st)
            ret[os.path.normpath(p.strip())] = sta
        return ret


    def get_ignore_allfiles(self):
        """Returns a set of all the ignored files in the repo"""
        raw = self._svn(self.path, ['status'], catchout=True, bytes=True)
#        logging.debug(raw)
        L = re.findall(r'^I\s*(.*?)\s*$', raw.decode('utf-8'), re.MULTILINE)
        return set(L)


    def get_remote_status(self):
        """Checks the status of the repo regarding sync state with remote branch.

        I'm not sure this make sense for SVN so we're just going to return 'sync'"""
        return 'sync'

    def get_branch(self):
        """Returns the current named branch, if this makes sense for the backend. None otherwise"""
        return None
        branch = self._svn(self.path, ['branch'], catchout=True)
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
        return self._svn(self.path, args, catchout=True)


    def get_raw_diff(self, refspec=None, filelist=None):
        """Gets the raw diff as a string"""
        args = ['diff', '--git']
        if refspec:  args = args + [refspec]
        if filelist: args = args + filelist
        return self._svn(self.path, args, catchout=True)


    def get_remote(self, rev=None):
        """Returns the url for the remote repo attached to head"""
        raw = self.get_info(rev=rev)
        L = re.findall('URL: (.*)\n', raw.decode('utf-8'))

        return L[0][0]


    def get_revision_id(self, rev=None):
        """Get a canonical key for the revision rev.

        This is just returning the rev for SVN"""
        if rev == None: rev = self.HEAD
        elif rev == self.INDEX: return None
        rev = self._sanitize_rev(rev)
        return rev


    def get_info(self, rev=None):
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


    def get_files(self, rev=None):
        """Gets a list of files in revision rev"""
        if rev == None: rev = self.HEAD
        rev = self._sanitize_rev(rev)

        raw = self._svn(self.path, ['ls', "-r", rev], catchout=True)
        return raw.split('\n')


# vim: expandtab:shiftwidth=4:tabstop=4:softtabstop=4:textwidth=80
