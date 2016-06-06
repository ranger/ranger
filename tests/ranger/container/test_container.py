from ranger.container import history


HISTORY_TEST_ENTRIES = [str(k) for k in range(20)]
OTHER_TEST_ENTRIES = [str(k) for k in range(40, 45)]

def testhistorybasic():
    # A history is a buffer of limited size that stores the last `maxlen`
    # item added to it. It has a `current` index that serves as a cursor.

    # A history has a limited size, check that only `maxlen` items are stored
    h = history.History(maxlen=10)
    for entry in HISTORY_TEST_ENTRIES:
        h.add(entry)

    # 10 items are stored
    assert len(h) == 10
    assert h.current() == "19"
    assert h.top() == "19"
    assert h.bottom() == "10"

    # going back in time affects only changes current item
    h.back()
    assert len(h) == 10
    assert h.current() == "18"
    assert h.top() == "19"
    assert h.bottom() == "10"

    # __iter__ is actually an interator and we can iterate through the list
    it = iter(h)
    assert iter(it) == it
    assert list(it) == HISTORY_TEST_ENTRIES[10:]

    # search allows to go back in time as long as a pattern matches and we don't
    # go over a step limit
    assert h.search("45", -9) == "18"
    assert h.search("1", -5) == "13"

    # fast forward selects the last item
    h.fast_forward()
    assert h.current() == "19"

    # back followed by forward is a noop
    h.back()
    h.forward()
    assert h.current() == "19"

    # move can be expressed as multiple calls to back and forward
    h.move(-3)
    h.forward()
    h.forward()
    h.forward()
    assert h.current() == "19"

    # back, forward, move play well with boundaries
    for _ in range(30):
        h.back()

    for _ in range(30):
        h.forward()

    for _ in range(30):
        h.move(-2)

    for _ in range(30):
        h.move(2)
    assert h.current() == "19"

    # we can create an history from another history
    h = history.History(maxlen=10)
    for entry in HISTORY_TEST_ENTRIES:
        h.add(entry)
    # XXX maxlen should not be used to refer to something that isn't a length
    otherh = history.History(maxlen=h)
    assert(list(h) == list(otherh))

    # Rebase replaces the past of the history with that of another
    otherh = history.History(maxlen=h)
    old_current_item = h.current()
    for entry in OTHER_TEST_ENTRIES:
        otherh.add(entry)
    assert list(otherh)[-3:] == ["42", "43", "44"]
    h.rebase(otherh)
    assert h.current() == old_current_item
    assert list(h)[-3:] == ['43', '44', old_current_item]

    # modify, modifies the top of the stack
    h.modify("23")
    assert h.current() == "23"


def testhistoryunique():
    # Check that unique history refuses to store duplicated entries
    h = history.History(maxlen=10, unique=True)
    for entry in HISTORY_TEST_ENTRIES:
        h.add(entry)
    assert h.current() == "19"
    h.add("17")
    assert list(h).count("17") == 1
    assert h.current() == "17"
