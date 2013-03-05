#!/usr/bin/env python
# Compatible with ranger 1.6.*
#
# This script searches image files in a directory, opens them all with sxiv and
# sets the first argument to the first image displayed by sxiv.
#
# This is supposed to be used in rifle.conf as a workaround for the fact that
# sxiv takes no file name arguments for the first image, just the number.  Copy
# this file somewhere into your $PATH and add this at the top of rifle.conf:
#
#   mime ^image, has sxiv, X, flag f = path/to/this/script -- "$@"
#
# Notes: 

import sys
import os
import subprocess
import mimetypes
import re

def usage_exit():
    print("Usage: " + sys.argv[0] + " PICTURES")
    sys.exit(0)

if len(sys.argv) == 1:
    usage_exit()
elif sys.argv[1] == "--":
    if len(sys.argv) >= 3:
        inputfile = sys.argv[2]
    else:
        usage_exit()
else:
    inputfile = sys.argv[1]

print(len(sys.argv))

## TODO:
## * support for selections
## * support for mimetypes.

inputdir = re.sub(r"/[^/]+$", "/", inputfile)
filelist = os.listdir(inputdir)

## Note: os.path.join seems to be slow.
# result = [a for a in filelist if v=mimetypes.guess_type(a)[0] and type(v) is str and v.find('image') != -1 ]
# result = [ inputdir + a for a in filelist if a.find('jpg') != -1 ]
result = [ inputdir + a for a in filelist if re.search('.(bmp|gif|jpe?g|png)$', a, re.IGNORECASE) != None ]

## TODO: Should sort and get count after concatenation.
list.sort(result)
try:
    count = result.index(inputfile) +1
except any:
    count = 0 +1

result.insert(0, "-n " + str(count) + " --")
result.insert(0, "sxiv")

subprocess.call(result)

