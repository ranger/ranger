# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""The TaskView allows you to modify what the loader is doing."""

from . import Widget
from ranger.ext.accumulator import Accumulator


class TaskView(Widget, Accumulator):
    old_lst = None

    def __init__(self, win):
        Widget.__init__(self, win)
        Accumulator.__init__(self)
        self.scroll_begin = 0

    def draw(self):
        base_clr = []
        base_clr.append('in_taskview')
        lst = self.get_list()

        if self.old_lst != lst:
            self.old_lst = lst
            self.need_redraw = True

        if self.need_redraw:
            self.win.erase()
            if not self.pointer_is_synced():
                self.sync_index()

            if self.hei <= 0:
                return

            self.addstr(0, 0, "Task View")
            self.color_at(0, 0, self.wid, tuple(base_clr), 'title')

            if lst:
                for i in range(self.hei - 1):
                    i += self.scroll_begin
                    try:
                        obj = lst[i]
                    except IndexError:
                        break

                    y = i + 1
                    clr = list(base_clr)

                    if self.pointer == i:
                        clr.append('selected')

                    descr = obj.get_description()
                    if obj.progressbar_supported and obj.percent >= 0 \
                            and obj.percent <= 100:
                        self.addstr(y, 0, "%3.2f%% - %s" %
                                (obj.percent, descr), self.wid)
                        wid = int(self.wid / 100.0 * obj.percent)
                        self.color_at(y, 0, self.wid, tuple(clr))
                        self.color_at(y, 0, wid, tuple(clr), 'loaded')
                    else:
                        self.addstr(y, 0, descr, self.wid)
                        self.color_at(y, 0, self.wid, tuple(clr))

            else:
                if self.hei > 1:
                    self.addstr(1, 0, "No task in the queue.")
                    self.color_at(1, 0, self.wid, tuple(base_clr), 'error')

            self.color_reset()

    def finalize(self):
        y = self.y + 1 + self.pointer - self.scroll_begin
        self.fm.ui.win.move(y, self.x)

    def task_remove(self, i=None):
        if i is None:
            i = self.pointer

        if self.fm.loader.queue:
            self.fm.loader.remove(index=i)

    def task_move(self, to, i=None):
        if i is None:
            i = self.pointer

        self.fm.loader.move(_from=i, to=to)

    def press(self, key):
        self.fm.ui.keymaps.use_keymap('taskview')
        self.fm.ui.press(key)

    def get_list(self):
        return self.fm.loader.queue
