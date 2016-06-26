import os
import time
import pytest

from ranger.container.bookmarks import Bookmarks


def testbookmarks(tmpdir):
    # Bookmarks point to directory location and allow fast access to
    # 'favorite' directories. They are persisted to a bookmark file, plain text.
    bookmarkfile = tmpdir.join("bookmarkfile")
    bmstore = Bookmarks(str(bookmarkfile))

    # loading an empty bookmark file doesnot crash
    bmstore.load()

    # One can add / remove and check existing of bookmark
    bmstore["h"] = "world"
    assert "h" in bmstore
    del bmstore["h"]

    # Only one letter/digit bookmarks are valid, adding something else fails
    # silently
    bmstore["hello"] = "world"
    assert "hello" not in bmstore

    # The default bookmark is ', remember allows to set it
    bmstore.remember("the milk")
    assert bmstore["'"] == "the milk"

    # We can persist bookmarks to disk and restore them from disk
    bmstore.save()
    secondstore = Bookmarks(str(bookmarkfile))
    secondstore.load()
    assert "'" in secondstore
    assert secondstore["'"] == "the milk"

    # We don't unnecessary update when the file on disk does not change
    origupdate = secondstore.update

    class OutOfDateException(Exception):
        pass

    def crash():
        raise OutOfDateException("Don't access me")
    secondstore.update = crash
    secondstore.update_if_outdated()

    # If the modification time change, we try to read the file
    newtime = time.time() - 5
    os.utime(str(bookmarkfile), (newtime, newtime))
    with pytest.raises(OutOfDateException):
        secondstore.update_if_outdated()
    secondstore.update = origupdate
    secondstore.update_if_outdated()
