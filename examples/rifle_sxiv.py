#!/usr/bin/env python
################################################################################
# Compatible with ranger 1.6.*
#
# This script does not use ranger API, it is completely independent.  Maybe it
# would be better and faster ro use ranger API, most notably to fetch the file
# list. The ranger 1.5.5 implementation of the sxiv app was as follow in
# ranger/default/apps.py:
#
# def app_sxiv(self, c):
# 	c.flags = 'd' + c.flags
# 	if len(c.files) is 1 and self.fm.env.cwd:
# 		images = [f.basename for f in self.fm.env.cwd.files if f.image]
# 		try:
# 			position = images.index(c.file.basename) + 1
# 		except:
# 			return None
# 		return 'sxiv', '-n', str(position), images
# 	return 'sxiv', c
#
#
# If only one file is selected, this script searches image files in a directory,
# opens them all with sxiv and sets the first argument to the first image
# displayed by sxiv.
#
# If a selection is on, this script will start sxiv over the selection only.
#
# This is supposed to be used in rifle.conf as a workaround for the fact that
# sxiv takes no file name arguments for the first image, just the number.  Copy
# this file somewhere into your $PATH and add this at the top of rifle.conf:
#
#   mime ^image, has sxiv, X, flag f = path/to/this/script -- "$@"
#
# This wrapper supports parameter, so if you want to start fullscreen and to fit
# all image to window, use
#
#   mime ^image, has sxiv, X, flag f = path/to/this/script -fs -- "$@"
################################################################################

import sys
import os
import subprocess
import mimetypes
import re

def usage():
    print("Usage: " + re.sub(r".*/", "", sys.argv[0])  + " PICTURES")

def is_image(a):
    v=mimetypes.guess_type(a)[0]
    if type(v) is str and v.find('image') != -1:
        return True
    return False

def sxiv_singlefile(inputfile):
    # Turn to an absolute path
    if inputfile[0] != '/':
        inputfile = os.path.abspath(inputfile)

    inputdir = re.sub(r"/[^/]+$", "/", inputfile)
    filelist = os.listdir(inputdir)
    filename = inputfile

    ## Note: os.path.join seems to be slow.
    result = [inputdir + a for a in filelist if is_image(a) ]
    list.sort(result)

    ## We get the index of the first argument to know where sxiv should start the display.
    try:
        count = result.index(inputfile) + 1
    except ValueError:
        count = 1

    result = ["-n" + str(count), "--"] + result
    if parameters:
        result = parameters + result
    result = ["sxiv"] + result

    subprocess.call(result)

def sxiv_multifile(arglist):
    result = [ os.path.abspath(a) for a in arglist ]
    list.sort(result)

    result = ["--"] + result
    if parameters:
        result = parameters + result
    result = ["sxiv"] + result

    subprocess.call(result)



################################################################################
## Parse arguments.
if len(sys.argv) == 1:
    usage_exit()

arglist = sys.argv
arglist.pop(0)

## Put all sxiv parameters in a string.
parameters = []
while len(arglist) != 0 and arglist[0] != "--" and arglist[0][0] == "-":
    parameters = parameters + [arglist[0]]
    arglist.pop(0)

if len(arglist) == 0:
    usage()
    sys.exit(0)

if arglist[0] == "--":
    arglist.pop(0)

if len(arglist) == 0:
    usage()
elif len(arglist) == 1:
    sxiv_singlefile(arglist[0])
elif len(arglist) >= 2:
    sxiv_multifile(arglist)

sys.exit(0)

################################################################################
# End
