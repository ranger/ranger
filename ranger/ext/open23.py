# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import absolute_import

from contextlib import contextmanager

from ranger import PY3


# COMPAT: We use the pattern of opening a file differently depending on the
#         python version in multiple places. Having calls to open in multiple
#         branches makes it impossible to use a with-statement instead. This
#         contextmanager hides away the lack of an errors keyword argument for
#         python 2 and is now preferred. This can be safely dropped once we
#         ditch python 2 support.
# pylint: disable=too-many-arguments
@contextmanager
def open23(
    file,
    mode="r",
    buffering=-1,
    encoding="UTF-8",
    errors=None,
    newline=None,
    closefd=True,
    opener=None,
):
    if PY3:
        fobj = open(
            file=file,
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
            closefd=closefd,
            opener=opener,
        )
    else:
        if buffering is None:
            # pylint: disable=unspecified-encoding
            fobj = open(name=file, mode=mode)
        else:
            # pylint: disable=unspecified-encoding
            fobj = open(name=file, mode=mode, buffering=buffering)
    try:
        yield fobj
    finally:
        fobj.close()
