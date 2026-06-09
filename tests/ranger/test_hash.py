from __future__ import (absolute_import, division, print_function)

from ranger.ext.hash import hash_chunks


def test_hash_chunks_accepts_directory_paths(tmp_path):
    directory = tmp_path / "directory"
    directory.mkdir()

    hashes = list(hash_chunks(str(directory)))

    assert len(hashes) == 1


def test_hash_chunks_recurses_with_full_child_paths(tmp_path):
    directory = tmp_path / "directory"
    directory.mkdir()
    (directory / "child.txt").write_text("content", encoding="utf-8")

    hashes = list(hash_chunks(str(directory)))

    assert len(hashes) >= 2
