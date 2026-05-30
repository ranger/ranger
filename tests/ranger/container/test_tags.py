from __future__ import (absolute_import, division, print_function)

import os
import pytest

from ranger.container.tags import Tags
from ranger.core.shared import FileManagerAware


class _StubFM(object):  # pylint: disable=too-few-public-methods
    """Minimal ``fm`` substitute for ``Tags`` -- only ``notify`` is exercised."""

    def notify(self, *args, **kwargs):
        pass


@pytest.fixture(autouse=True)
def _fm_stub():
    # ``Tags`` inherits from ``FileManagerAware`` and calls ``self.fm.notify``
    # from its IO helpers; install a no-op stub for the duration of each test.
    previous_fm = getattr(FileManagerAware, "fm", None)
    FileManagerAware.fm_set(_StubFM())
    yield
    if previous_fm is None:
        try:
            del FileManagerAware.fm
        except AttributeError:
            pass
    else:
        FileManagerAware.fm_set(previous_fm)


def _write_tagfile(tmpdir, lines):
    tagfile = tmpdir.join("tagged")
    tagfile.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
    return str(tagfile)


def test_update_path_renames_single_tag(tmpdir):
    # Regression test for issue #3176: renaming a tagged file used to raise
    # ``RuntimeError: dictionary keys changed during iteration`` because
    # ``update_path`` mutated ``self.tags`` while iterating over it, which
    # also meant the rename was never persisted to disk.
    tagfile = _write_tagfile(tmpdir, ["/tmp/abcd"])
    tags = Tags(tagfile)

    tags.update_path("/tmp/abcd", "/tmp/efgh")

    assert tags.tags == {"/tmp/efgh": "*"}
    # The new path must also be persisted, otherwise the tag is silently
    # forgotten the next time ranger re-reads the tag file.
    with open(tagfile, encoding="utf-8") as fobj:
        assert fobj.read() == "/tmp/efgh\n"


def test_update_path_renames_directory_prefix(tmpdir):
    # Renaming a directory should rewrite every tagged path that lives under
    # it while leaving unrelated paths alone, and should preserve custom tag
    # characters.
    tagfile = _write_tagfile(tmpdir, [
        "/tmp/foo/file1",
        "a:/tmp/foo/file2",
        "/tmp/bar/file3",
        "b:/tmp/foo/sub/file4",
    ])
    tags = Tags(tagfile)

    tags.update_path("/tmp/foo", "/new/foo")

    assert tags.tags == {
        "/new/foo/file1": "*",
        "/new/foo/file2": "a",
        "/tmp/bar/file3": "*",
        "/new/foo/sub/file4": "b",
    }


def test_update_path_noop_does_not_rewrite_file(tmpdir):
    # If nothing matches, the tag file should not be rewritten -- the
    # ``changed`` flag is what gates ``dump()``.
    tagfile = _write_tagfile(tmpdir, ["/tmp/abcd"])
    tags = Tags(tagfile)
    original_mtime = os.path.getmtime(tagfile)

    tags.update_path("/nowhere", "/elsewhere")

    assert tags.tags == {"/tmp/abcd": "*"}
    assert os.path.getmtime(tagfile) == original_mtime


def test_update_path_does_not_rename_partial_prefix_match(tmpdir):
    # ``/tmp/foo`` must not match ``/tmp/foobar`` -- the separator boundary
    # check exists for exactly this reason and we want a test that pins it.
    tagfile = _write_tagfile(tmpdir, ["/tmp/foobar/file"])
    tags = Tags(tagfile)

    tags.update_path("/tmp/foo", "/new/foo")

    assert tags.tags == {"/tmp/foobar/file": "*"}
