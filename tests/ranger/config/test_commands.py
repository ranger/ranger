from __future__ import (absolute_import, division, print_function)

import os
import sys
import tempfile
import types

import pytest

from ranger.config.commands import bulkrename


class _File(object):  # pylint: disable=too-few-public-methods

    def __init__(self, path):
        self.path = path


class _Tags(object):

    def __init__(self, path):
        self.tags = {path: "*"}
        self.dumped = False

    def __contains__(self, path):
        return path in self.tags

    def remove(self, path):
        del self.tags[path]

    def dump(self):
        self.dumped = True


class _FM(object):

    def __init__(self, path, edit_script=False):
        self.path = path
        self.thisdir = self
        self.thistab = self
        self.tags = _Tags(path + "/old")
        self.notifications = []
        self._edit_script = edit_script
        self._editor_calls = 0

    def get_selection(self):
        return [type("SelectedFile", (object,), {"relative_path": "old"})()]

    def execute_file(self, files, app):
        assert app == "editor"
        self._editor_calls += 1
        if self._editor_calls == 1:
            with open(files[0].path, "wb") as fobj:
                fobj.write(b"new")
        elif self._edit_script:
            with open(files[0].path, "ab") as fobj:
                fobj.write(b"# edited\n")

    def run(self, command, flags):
        assert command[0] == "/bin/sh"
        assert flags == "w"

    def notify(self, message):
        self.notifications.append(message)


@pytest.fixture
def reopenable_tempfiles(monkeypatch):
    original = tempfile.NamedTemporaryFile
    paths = []
    file_module = types.ModuleType("ranger.container.file")
    file_module.File = _File

    def named_temporary_file(*args, **kwargs):
        kwargs["delete"] = False
        fobj = original(*args, **kwargs)  # pylint: disable=consider-using-with
        paths.append(fobj.name)
        return fobj

    monkeypatch.setattr(tempfile, "NamedTemporaryFile", named_temporary_file)
    monkeypatch.setitem(sys.modules, "ranger.container.file", file_module)
    yield
    for path in paths:
        if os.path.exists(path):
            os.unlink(path)


@pytest.mark.usefixtures("reopenable_tempfiles")
def test_bulkrename_unchanged_script_retags_files(tmpdir):
    fm = _FM(str(tmpdir))
    command = bulkrename("bulkrename")
    command.fm = fm

    command.execute()

    assert fm.tags.tags == {str(tmpdir) + "/new": "*"}
    assert fm.tags.dumped
    assert not fm.notifications


@pytest.mark.usefixtures("reopenable_tempfiles")
def test_bulkrename_edited_script_notifies_without_retagging(tmpdir):
    fm = _FM(str(tmpdir), edit_script=True)
    command = bulkrename("bulkrename")
    command.fm = fm

    command.execute()

    assert fm.tags.tags == {str(tmpdir) + "/old": "*"}
    assert not fm.tags.dumped
    assert fm.notifications == ["files have not been retagged"]
