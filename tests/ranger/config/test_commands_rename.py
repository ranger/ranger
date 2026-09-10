"""Tests for the rename command — regression for issue #3175.

When renaming a file in a directory accessed via a symlink, the cursor
must move to the renamed file.  The bug was caused by File(new_name)
resolving the path via os.getcwd() (physical path) while the directory's
internal file list uses the logical path (preserving symlinks).
"""

from __future__ import absolute_import, division, print_function

import os
import sys

from ranger.container.file import File
from ranger.core.shared import FileManagerAware

# Make ranger importable from the source tree
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


# ---------------------------------------------------------------------------
# Helpers: lightweight FM mock
# ---------------------------------------------------------------------------

class _MockBookmarks(object):  # pylint: disable=too-few-public-methods
    def update_path(self, old, new):
        pass


class _MockTags(object):  # pylint: disable=too-few-public-methods
    def update_path(self, old, new):
        pass


class _MockNotify(object):  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.last_message = None
        self.last_bad = None

    def __call__(self, msg, bad=False):
        self.last_message = msg
        self.last_bad = bad


class _MockDir(object):  # pylint: disable=too-few-public-methods
    """Minimal stand-in for ranger.container.directory.Directory."""

    def __init__(self, path):
        self.path = path
        self.pointed_obj = None


class _MockFM(object):  # pylint: disable=too-few-public-methods
    """Minimal FM mock that satisfies rename's dependencies."""

    def __init__(self, thisdir, thisfile):
        self.thisdir = thisdir
        self.thisfile = thisfile
        self.bookmarks = _MockBookmarks()
        self.tags = _MockTags()
        self.notify = _MockNotify()

    def rename(self, src, dest):
        if hasattr(src, 'path'):
            src = src.path
        try:
            os.makedirs(os.path.dirname(dest))
        except OSError:
            pass
        try:
            os.rename(src, dest)
        except OSError as err:
            self.notify(err)
            return False
        return True


def _make_rename_cmd(fm, arg_string):
    """Instantiate the rename command with the given argument string."""
    from ranger.config import commands as cmds

    FileManagerAware.fm = fm

    cmd = cmds.rename("rename " + arg_string)
    cmd.fm = fm
    return cmd


# ===================================================================
# Test 1: rename in a normal directory (no symlink) — baseline
# ===================================================================

def test_rename_normal_directory(tmpdir):
    """Renaming in a regular directory must move the cursor."""
    real = str(tmpdir.join("real"))
    os.mkdir(real)
    file1 = os.path.join(real, "alpha")
    with open(file1, "w", encoding="utf-8") as fobj:
        fobj.write("data")

    thisdir = _MockDir(real)
    thisfile = File(file1, path_is_abs=True)
    fm = _MockFM(thisdir, thisfile)
    cmd = _make_rename_cmd(fm, "beta")

    result = cmd.execute()
    assert result is None, "rename should succeed (return None)"

    assert os.path.exists(os.path.join(real, "beta"))
    assert not os.path.exists(file1)

    assert fm.thisdir.pointed_obj is not None
    assert fm.thisfile.basename == "beta"
    assert fm.thisfile.path == os.path.join(real, "beta")


# ===================================================================
# Test 2: THE BUG — rename under a symlink (issue #3175)
# ===================================================================

def test_rename_under_symlink(tmpdir):
    """Renaming under a symlink must move the cursor.

    This is the exact reproduction scenario from the issue:
    - real dir:  tmpdir/a
    - symlink:   tmpdir/b -> a
    - cd b, rename file -> cursor must follow
    """
    real = str(tmpdir.join("a"))
    os.mkdir(real)
    symlink = str(tmpdir.join("b"))
    os.symlink(real, symlink)

    file2 = os.path.join(symlink, "two")
    with open(file2, "w", encoding="utf-8") as fobj:
        fobj.write("data")

    thisdir = _MockDir(symlink)
    thisfile = File(file2, path_is_abs=True)
    fm = _MockFM(thisdir, thisfile)

    old_cwd = os.getcwd()
    try:
        os.chdir(real)
        cmd = _make_rename_cmd(fm, "four")
        cmd.execute()
    finally:
        os.chdir(old_cwd)

    assert os.path.exists(os.path.join(real, "four"))
    assert not os.path.exists(file2)

    assert fm.thisdir.pointed_obj is not None
    assert fm.thisfile.basename == "four"
    assert fm.thisfile.path == os.path.join(symlink, "four"), (
        "Expected path via symlink ({0}/four) but got {1}".format(
            symlink, fm.thisfile.path
        )
    )


# ===================================================================
# Test 3: rename to same name — no-op
# ===================================================================

def test_rename_same_name(tmpdir):
    """Renaming to the same name should be a no-op."""
    real = str(tmpdir.join("d"))
    os.mkdir(real)
    file1 = os.path.join(real, "keepme")
    with open(file1, "w", encoding="utf-8") as fobj:
        fobj.write("data")

    thisdir = _MockDir(real)
    thisfile = File(file1, path_is_abs=True)
    fm = _MockFM(thisdir, thisfile)
    cmd = _make_rename_cmd(fm, "keepme")

    result = cmd.execute()
    assert result is None
    assert os.path.exists(file1)
    assert fm.thisdir.pointed_obj is None


# ===================================================================
# Test 4: rename to existing name — error
# ===================================================================

def test_rename_existing_name(tmpdir):
    """Renaming to a name that already exists should fail."""
    real = str(tmpdir.join("d"))
    os.mkdir(real)
    file1 = os.path.join(real, "src")
    file2 = os.path.join(real, "dst")
    for p in (file1, file2):
        with open(p, "w", encoding="utf-8") as fobj:
            fobj.write("data")

    thisdir = _MockDir(real)
    thisfile = File(file1, path_is_abs=True)
    fm = _MockFM(thisdir, thisfile)
    cmd = _make_rename_cmd(fm, "dst")

    cmd.execute()
    assert fm.notify.last_bad is True
    assert os.path.exists(file1)


# ===================================================================
# Test 5: rename with no argument — error
# ===================================================================

def test_rename_no_argument(tmpdir):
    """Renaming without an argument should notify error."""
    real = str(tmpdir.join("d"))
    os.mkdir(real)

    thisdir = _MockDir(real)
    thisfile = File(os.path.join(real, "x"), path_is_abs=True)
    fm = _MockFM(thisdir, thisfile)
    cmd = _make_rename_cmd(fm, "")

    cmd.execute()
    assert fm.notify.last_bad is True


# ===================================================================
# Test 6: rename under symlink — path matches directory list
# ===================================================================

def test_rename_symlink_path_matches_directory_list(tmpdir):
    """Verify the File object path scheme matches how Directory builds paths.

    Directory.load_bit_by_bit creates files as:
        File(self.path + '/' + filename, path_is_abs=True, ...)
    where self.path is the *logical* (symlink) path.

    After rename, the new File's path must follow the same scheme so that
    Directory.sync_index can locate it via path comparison.
    """
    real = str(tmpdir.join("inner"))
    os.mkdir(real)
    symlink = str(tmpdir.join("link"))
    os.symlink(real, symlink)

    file1 = os.path.join(symlink, "oldname")
    with open(file1, "w", encoding="utf-8") as fobj:
        fobj.write("data")

    thisdir = _MockDir(symlink)
    thisfile = File(file1, path_is_abs=True)
    fm = _MockFM(thisdir, thisfile)

    old_cwd = os.getcwd()
    try:
        os.chdir(real)
        cmd = _make_rename_cmd(fm, "newname")
        cmd.execute()
    finally:
        os.chdir(old_cwd)

    expected_path = os.path.join(symlink, "newname")
    assert fm.thisfile.path == expected_path

    wrong_path = os.path.join(real, "newname")
    assert fm.thisfile.path != wrong_path, (
        "Path should use logical (symlink) path, not physical path"
    )


# ===================================================================
# Test 7: rename into a subdirectory under symlink
# ===================================================================

def test_rename_into_subdir_under_symlink(tmpdir):
    """Renaming into a subdirectory should still use logical paths."""
    real = str(tmpdir.join("a"))
    os.mkdir(real)
    subdir = os.path.join(real, "sub")
    os.mkdir(subdir)
    symlink = str(tmpdir.join("b"))
    os.symlink(real, symlink)

    file1 = os.path.join(symlink, "src.txt")
    with open(file1, "w", encoding="utf-8") as fobj:
        fobj.write("data")

    thisdir = _MockDir(symlink)
    thisfile = File(file1, path_is_abs=True)
    fm = _MockFM(thisdir, thisfile)

    cmd = _make_rename_cmd(fm, "sub/dst.txt")
    cmd.execute()

    assert os.path.exists(os.path.join(real, "sub", "dst.txt"))
    assert fm.thisfile.path == os.path.join(symlink, "sub", "dst.txt")


# ===================================================================
# Test 8: rename with absolute destination path
# ===================================================================

def test_rename_absolute_destination(tmpdir):
    """Renaming to an absolute path should work correctly."""
    real = str(tmpdir.join("src_dir"))
    os.mkdir(real)
    dest_dir = str(tmpdir.join("dest_dir"))
    os.mkdir(dest_dir)

    file1 = os.path.join(real, "mover_me")
    with open(file1, "w", encoding="utf-8") as fobj:
        fobj.write("data")

    thisdir = _MockDir(real)
    thisfile = File(file1, path_is_abs=True)
    fm = _MockFM(thisdir, thisfile)

    abs_dest = os.path.join(dest_dir, "moved")
    cmd = _make_rename_cmd(fm, abs_dest)
    cmd.execute()

    assert os.path.exists(abs_dest)
    assert not os.path.exists(file1)
    assert fm.thisfile.path == abs_dest


# ===================================================================
# Test 9: original bug scenario — exact reproduction
# ===================================================================

def test_issue_3175_exact_reproduction(tmpdir):
    """Exact steps from the issue report.

    1. mkdir a, ln -s a b
    2. touch a/1 a/2
    3. cd a; rename 1->3  (should work)
    4. cd b; rename 2->4  (cursor must follow)
    """
    a = str(tmpdir.join("a"))
    os.mkdir(a)
    b = str(tmpdir.join("b"))
    os.symlink(a, b)

    for name in ("1", "2"):
        with open(os.path.join(a, name), "w", encoding="utf-8") as fobj:
            fobj.write("")

    # Step 3: rename in real directory
    thisdir_a = _MockDir(a)
    thisfile_1 = File(os.path.join(a, "1"), path_is_abs=True)
    fm_a = _MockFM(thisdir_a, thisfile_1)
    cmd3 = _make_rename_cmd(fm_a, "3")
    cmd3.execute()
    assert fm_a.thisfile.basename == "3"
    assert fm_a.thisfile.path == os.path.join(a, "3")

    # Step 4: rename in symlinked directory
    thisdir_b = _MockDir(b)
    thisfile_2 = File(os.path.join(b, "2"), path_is_abs=True)
    fm_b = _MockFM(thisdir_b, thisfile_2)

    old_cwd = os.getcwd()
    try:
        os.chdir(a)
        cmd4 = _make_rename_cmd(fm_b, "4")
        cmd4.execute()
    finally:
        os.chdir(old_cwd)

    assert os.path.exists(os.path.join(a, "4"))
    assert not os.path.exists(os.path.join(a, "2"))

    assert fm_b.thisfile.basename == "4"
    assert fm_b.thisfile.path == os.path.join(b, "4"), (
        "BUG NOT FIXED: cursor path is {0}, expected {1}/4".format(
            fm_b.thisfile.path, b
        )
    )
