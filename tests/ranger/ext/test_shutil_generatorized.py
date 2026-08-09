from __future__ import (absolute_import, division, print_function)

import os

from ranger.ext.shutil_generatorized import move


def consume(generator):
    for _ in generator:
        pass


# === Core regression: exact scenario from issue #3145 ===


def test_move_symlink_into_target_directory(tmpdir):
    """Regression test for #3145.

    Setup:  directory A, symlink B -> A
    Action: move B into A
    Before fix: IsADirectoryError
    After fix:  B appears inside A, still a symlink
    """
    dir_a = str(tmpdir.join("A"))
    os.mkdir(dir_a)
    symlink_b = str(tmpdir.join("B"))
    os.symlink(dir_a, symlink_b)

    consume(move(symlink_b, dir_a))

    dst_link = os.path.join(dir_a, "B")
    assert os.path.islink(dst_link), "B should be a symlink inside A"
    assert os.path.samefile(dir_a, dst_link), "B should still point to A"
    assert not os.path.lexists(symlink_b), "Original B should no longer exist"


def test_move_symlink_into_symlink_to_directory(tmpdir):
    """Move symlink into a directory accessed via another symlink."""
    dir_a = str(tmpdir.join("A"))
    os.mkdir(dir_a)
    symlink_b = str(tmpdir.join("B"))
    os.symlink(dir_a, symlink_b)
    dst_link = str(tmpdir.join("C_link"))
    os.symlink(dir_a, dst_link)

    consume(move(symlink_b, dst_link))

    moved = os.path.join(dst_link, "B")
    assert os.path.islink(moved)
    assert not os.path.lexists(symlink_b)


# === Regression: ensure existing functionality is not broken ===


def test_move_regular_file(tmpdir):
    """Regression: regular file into directory."""
    src = tmpdir.join("file.txt")
    src.write("hello")
    dst_dir = str(tmpdir.join("dest"))
    os.mkdir(dst_dir)

    consume(move(str(src), dst_dir))

    moved = os.path.join(dst_dir, "file.txt")
    assert os.path.isfile(moved)
    assert not os.path.exists(str(src))
    with open(moved, encoding="utf-8") as f:
        assert f.read() == "hello"


def test_move_directory(tmpdir):
    """Regression: directory into another directory."""
    src_dir = tmpdir.join("srcdir")
    src_dir.mkdir()
    src_dir.join("inner.txt").write("data")
    dst_dir = tmpdir.join("dstdir")
    dst_dir.mkdir()

    consume(move(str(src_dir), str(dst_dir)))

    moved = os.path.join(str(dst_dir), "srcdir")
    assert os.path.isdir(moved)
    assert os.path.isfile(os.path.join(moved, "inner.txt"))
    assert not os.path.exists(str(src_dir))


def test_move_file_to_file(tmpdir):
    """Regression: rename (dst is not a directory)."""
    src = tmpdir.join("original.txt")
    src.write("content")
    dst = str(tmpdir.join("renamed.txt"))

    consume(move(str(src), dst))

    assert os.path.isfile(dst)
    assert not os.path.exists(str(src))
    with open(dst, encoding="utf-8") as f:
        assert f.read() == "content"


def test_move_symlink_into_unrelated_directory(tmpdir):
    """Symlink moved into a directory it does NOT point to."""
    dir_a = str(tmpdir.join("A"))
    os.mkdir(dir_a)
    dir_b = str(tmpdir.join("B"))
    os.mkdir(dir_b)
    symlink_c = str(tmpdir.join("C"))
    os.symlink(dir_a, symlink_c)

    consume(move(symlink_c, dir_b))

    moved = os.path.join(dir_b, "C")
    assert os.path.islink(moved)
    assert os.path.samefile(dir_a, moved)
    assert not os.path.lexists(symlink_c)


def test_move_broken_symlink_into_directory(tmpdir):
    """Edge case: dangling symlink moved into a directory."""
    dst_dir = str(tmpdir.join("dest"))
    os.mkdir(dst_dir)
    broken = str(tmpdir.join("broken_link"))
    os.symlink("/nonexistent/path/that/does/not/exist", broken)

    consume(move(broken, dst_dir))

    moved = os.path.join(dst_dir, "broken_link")
    assert os.path.islink(moved), "Broken symlink should be moved as-is"
    assert not os.path.exists(moved), "Target still doesn't exist"
    assert not os.path.lexists(broken), "Original link removed"


def test_move_symlink_to_file_into_directory(tmpdir):
    """Symlink pointing to a regular file, moved into a directory."""
    real_file = tmpdir.join("real.txt")
    real_file.write("data")
    symlink = str(tmpdir.join("link_to_file"))
    os.symlink(str(real_file), symlink)
    dst_dir = str(tmpdir.join("dest"))
    os.mkdir(dst_dir)

    consume(move(symlink, dst_dir))

    moved = os.path.join(dst_dir, "link_to_file")
    assert os.path.islink(moved)
    with open(moved, encoding="utf-8") as f:
        assert f.read() == "data"
    assert not os.path.lexists(symlink)
