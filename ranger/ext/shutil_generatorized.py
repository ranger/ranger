# This file was taken from the python standard library and has been
# slightly modified to do a "yield" after every 16KB of copying
"""Utility functions for copying files and directory trees.

XXX The functions here don't copy the resource fork or other metadata on Mac.
"""

import os
import sys
import stat
from os.path import abspath

__all__ = ["copyfileobj", "copyfile", "copystat", "copy2", "BLOCK_SIZE",
           "copytree", "move", "rmtree", "Error", "SpecialFileError"]

APPENDIX = '_'
BLOCK_SIZE = 16 * 1024


class Error(EnvironmentError):
    pass


class SpecialFileError(EnvironmentError):
    """Raised when trying to do a kind of operation (e.g. copying) which is
    not supported on a special file (e.g. a named pipe)"""

try:
    WindowsError
except NameError:
    WindowsError = None


def copyfileobj(fsrc, fdst, length=BLOCK_SIZE):
    """copy data from file-like object fsrc to file-like object fdst"""
    done = 0
    while 1:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)
        done += len(buf)
        yield done


def _samefile(src, dst):
    # Macintosh, Unix.
    if hasattr(os.path, 'samefile'):
        try:
            return os.path.samefile(src, dst)
        except OSError:
            return False

    # All other platforms: check for same pathname.
    return (os.path.normcase(abspath(src)) ==
            os.path.normcase(abspath(dst)))


def copyfile(src, dst):
    """Copy data from src to dst"""
    if _samefile(src, dst):
        raise Error("`%s` and `%s` are the same file" % (src, dst))

    fsrc = None
    fdst = None
    for fn in [src, dst]:
        try:
            st = os.stat(fn)
        except OSError:
            # File most likely does not exist
            pass
        else:
            # XXX What about other special files? (sockets, devices...)
            if stat.S_ISFIFO(st.st_mode):
                raise SpecialFileError("`%s` is a named pipe" % fn)
    try:
        fsrc = open(src, 'rb')
        fdst = open(dst, 'wb')
        for done in copyfileobj(fsrc, fdst):
            yield done
    finally:
        if fdst:
            fdst.close()
        if fsrc:
            fsrc.close()


def copystat(src, dst):
    """Copy all stat info (mode bits, atime, mtime, flags) from src to dst"""
    st = os.lstat(src)
    mode = stat.S_IMODE(st.st_mode)
    if hasattr(os, 'utime'):
        try:
            os.utime(dst, (st.st_atime, st.st_mtime))
        except:
            pass
    if hasattr(os, 'chmod'):
        try:
            os.chmod(dst, mode)
        except:
            pass
    if hasattr(os, 'chflags') and hasattr(st, 'st_flags'):
        try:
            os.chflags(dst, st.st_flags)
        except:
            pass


def copy2(src, dst, overwrite=False, symlinks=False):
    """Copy data and all stat info ("cp -p src dst").

    The destination may be a directory.

    """
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    if not overwrite:
        dst = get_safe_path(dst)
    if symlinks and os.path.islink(src):
        linkto = os.readlink(src)
        if overwrite and os.path.lexists(dst):
            os.unlink(dst)
        os.symlink(linkto, dst)
    else:
        for done in copyfile(src, dst):
            yield done
        copystat(src, dst)


def get_safe_path(dst):
    if not os.path.exists(dst):
        return dst
    if not dst.endswith(APPENDIX):
        dst += APPENDIX
        if not os.path.exists(dst):
            return dst
    n = 0
    test_dst = dst + str(n)
    while os.path.exists(test_dst):
        n += 1
        test_dst = dst + str(n)

    return test_dst


def copytree(src, dst, symlinks=False, ignore=None, overwrite=False):
    """Recursively copy a directory tree using copy2().

    The destination directory must not already exist.
    If exception(s) occur, an Error is raised with a list of reasons.

    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied.

    The optional ignore argument is a callable. If given, it
    is called with the `src` parameter, which is the directory
    being visited by copytree(), and `names` which is the list of
    `src` contents, as returned by os.listdir():

        callable(src, names) -> ignored_names

    Since copytree() is called recursively, the callable will be
    called once for each directory that is copied. It returns a
    list of names relative to the `src` directory that should
    not be copied.

    XXX Consider this example code rather than the ultimate tool.

    """
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    errors = []
    try:
        os.makedirs(dst)
    except Exception as err:
        if not overwrite:
            dst = get_safe_path(dst)
            os.makedirs(dst)
    done = 0
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                if overwrite and os.path.lexists(dstname):
                    os.unlink(dstname)
                os.symlink(linkto, dstname)
                copystat(srcname, dstname)
            elif os.path.isdir(srcname):
                d = 0
                for d in copytree(srcname, dstname, symlinks,
                        ignore, overwrite):
                    yield done + d
                done += d
            else:
                # Will raise a SpecialFileError for unsupported file types
                d = 0
                for d in copy2(srcname, dstname,
                        overwrite=overwrite, symlinks=symlinks):
                    yield done + d
                done += d
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            errors.extend(err.args[0])
        except EnvironmentError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        copystat(src, dst)
    except OSError as why:
        if WindowsError is not None and isinstance(why, WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.extend((src, dst, str(why)))
    if errors:
        raise Error(errors)


def rmtree(path, ignore_errors=False, onerror=None):
    """Recursively delete a directory tree.

    If ignore_errors is set, errors are ignored; otherwise, if onerror
    is set, it is called to handle the error with arguments (func,
    path, exc_info) where func is os.listdir, os.remove, or os.rmdir;
    path is the argument to that function that caused it to fail; and
    exc_info is a tuple returned by sys.exc_info().  If ignore_errors
    is false and onerror is None, an exception is raised.

    """
    if ignore_errors:
        def onerror(*args):
            pass
    elif onerror is None:
        def onerror(*args):
            raise
    try:
        if os.path.islink(path):
            # symlinks to directories are forbidden, see bug #1669
            raise OSError("Cannot call rmtree on a symbolic link")
    except OSError:
        onerror(os.path.islink, path, sys.exc_info())
        # can't continue even if onerror hook returns
        return
    names = []
    try:
        names = os.listdir(path)
    except os.error as err:
        onerror(os.listdir, path, sys.exc_info())
    for name in names:
        fullname = os.path.join(path, name)
        try:
            mode = os.lstat(fullname).st_mode
        except os.error:
            mode = 0
        if stat.S_ISDIR(mode):
            rmtree(fullname, ignore_errors, onerror)
        else:
            try:
                os.remove(fullname)
            except os.error as err:
                onerror(os.remove, fullname, sys.exc_info())
    try:
        os.rmdir(path)
    except os.error:
        onerror(os.rmdir, path, sys.exc_info())


def _basename(path):
    # A basename() variant which first strips the trailing slash, if present.
    # Thus we always get the last component of the path, even for directories.
    return os.path.basename(path.rstrip(os.path.sep))


def move(src, dst, overwrite=False):
    """Recursively move a file or directory to another location. This is
    similar to the Unix "mv" command.

    If the destination is a directory or a symlink to a directory, the source
    is moved inside the directory. The destination path must not already
    exist.

    If the destination already exists but is not a directory, it may be
    overwritten depending on os.rename() semantics.

    If the destination is on our current filesystem, then rename() is used.
    Otherwise, src is copied to the destination and then removed.
    A lot more could be done here...  A look at a mv.c shows a lot of
    the issues this implementation glosses over.

    """
    real_dst = os.path.join(dst, _basename(src))
    if not overwrite:
        real_dst = get_safe_path(real_dst)
    try:
        os.rename(src, real_dst)
    except OSError:
        if os.path.isdir(src):
            if _destinsrc(src, dst):
                raise Error("Cannot move a directory '%s' into itself '%s'." % (src, dst))
            for done in copytree(src, real_dst, symlinks=True, overwrite=overwrite):
                yield done
            rmtree(src)
        else:
            for done in copy2(src, real_dst, symlinks=True, overwrite=overwrite):
                yield done
            os.unlink(src)


def _destinsrc(src, dst):
    src = abspath(src)
    dst = abspath(dst)
    if not src.endswith(os.path.sep):
        src += os.path.sep
    if not dst.endswith(os.path.sep):
        dst += os.path.sep
    return dst.startswith(src)

# vi: expandtab sts=4 ts=4 sw=4
