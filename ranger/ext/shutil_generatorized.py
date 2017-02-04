# This file was taken from the python 2.7.13 standard library and has been
# slightly modified to do a "yield" after every 16KB of copying

from __future__ import (absolute_import, division, print_function)

import os
import stat
import sys
from shutil import (_samefile, rmtree, _basename, _destinsrc, Error, SpecialFileError)

__all__ = ["copyfileobj", "copyfile", "copystat", "copy2", "BLOCK_SIZE",
           "copytree", "move", "rmtree", "Error", "SpecialFileError"]

APPENDIX = '_'
BLOCK_SIZE = 16 * 1024


try:
    WindowsError
except NameError:
    WindowsError = None  # pylint: disable=invalid-name


if sys.version_info < (3, 3):
    def copystat(src, dst):
        """Copy all stat info (mode bits, atime, mtime, flags) from src to dst"""
        st = os.stat(src)  # pylint: disable=invalid-name
        mode = stat.S_IMODE(st.st_mode)
        if hasattr(os, 'utime'):
            try:
                os.utime(dst, (st.st_atime, st.st_mtime))
            except OSError:
                pass
        if hasattr(os, 'chmod'):
            try:
                os.chmod(dst, mode)
            except OSError:
                pass
        if hasattr(os, 'chflags') and hasattr(st, 'st_flags'):
            try:
                os.chflags(dst, st.st_flags)  # pylint: disable=no-member
            except OSError:
                pass
else:
    from shutil import _copyxattr  # pylint: disable=no-name-in-module

    def copystat(src, dst, follow_symlinks=True):
        """Copy all stat info (mode bits, atime, mtime, flags) from src to dst.

        If the optional flag `follow_symlinks` is not set, symlinks aren't followed if and
        only if both `src` and `dst` are symlinks.

        """
        def _nop(*args, **kwargs):  # pylint: disable=unused-argument
            pass

        # follow symlinks (aka don't not follow symlinks)
        follow = follow_symlinks or not (os.path.islink(src) and os.path.islink(dst))
        if follow:
            # use the real function if it exists
            def lookup(name):
                return getattr(os, name, _nop)
        else:
            # use the real function only if it exists
            # *and* it supports follow_symlinks
            def lookup(name):
                fn = getattr(os, name, _nop)  # pylint: disable=invalid-name
                if fn in os.supports_follow_symlinks:  # pylint: disable=no-member
                    return fn
                return _nop

        st = lookup("stat")(src, follow_symlinks=follow)  # pylint: disable=invalid-name
        mode = stat.S_IMODE(st.st_mode)
        try:
            lookup("utime")(dst, ns=(st.st_atime_ns, st.st_mtime_ns),
                            follow_symlinks=follow)
        except OSError:
            pass
        try:
            lookup("chmod")(dst, mode, follow_symlinks=follow)
        except NotImplementedError:
            # if we got a NotImplementedError, it's because
            #   * follow_symlinks=False,
            #   * lchown() is unavailable, and
            #   * either
            #       * fchownat() is unavailable or
            #       * fchownat() doesn't implement AT_SYMLINK_NOFOLLOW.
            #         (it returned ENOSUP.)
            # therefore we're out of options--we simply cannot chown the
            # symlink.  give up, suppress the error.
            # (which is what shutil always did in this circumstance.)
            pass
        except OSError:
            pass
        if hasattr(st, 'st_flags'):
            try:
                lookup("chflags")(dst, st.st_flags, follow_symlinks=follow)
            except OSError:
                pass
        try:
            _copyxattr(src, dst, follow_symlinks=follow)
        except OSError:
            pass


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


def copyfile(src, dst):
    """Copy data from src to dst"""
    if _samefile(src, dst):
        raise Error("`%s` and `%s` are the same file" % (src, dst))

    for fn in [src, dst]:  # pylint: disable=invalid-name
        try:
            st = os.stat(fn)  # pylint: disable=invalid-name
        except OSError:
            # File most likely does not exist
            pass
        else:
            # XXX What about other special files? (sockets, devices...)
            if stat.S_ISFIFO(st.st_mode):
                raise SpecialFileError("`%s` is a named pipe" % fn)

    with open(src, 'rb') as fsrc:
        with open(dst, 'wb') as fdst:
            for done in copyfileobj(fsrc, fdst):
                yield done


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


def copytree(src, dst,  # pylint: disable=too-many-locals,too-many-branches
             symlinks=False, ignore=None, overwrite=False):
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

    try:
        os.makedirs(dst)
    except OSError:
        if not overwrite:
            dst = get_safe_path(dst)
            os.makedirs(dst)
    errors = []
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
                n = 0
                for n in copytree(srcname, dstname, symlinks, ignore, overwrite):
                    yield done + n
                done += n
            else:
                # Will raise a SpecialFileError for unsupported file types
                n = 0
                for n in copy2(srcname, dstname, overwrite=overwrite, symlinks=symlinks):
                    yield done + n
                done += n
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
            errors.append((src, dst, str(why)))
    if errors:
        raise Error(errors)


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
    real_dst = dst
    if os.path.isdir(dst):
        if _samefile(src, dst):
            # We might be on a case insensitive filesystem,
            # perform the rename anyway.
            os.rename(src, dst)
            return

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
