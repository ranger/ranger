# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

from collections import deque
from subprocess import Popen, PIPE
from time import time, sleep
import math
import os.path
import select
import errno

try:
    import chardet  # pylint: disable=import-error
    HAVE_CHARDET = True
except ImportError:
    HAVE_CHARDET = False

from ranger import PY3
from ranger.core.shared import FileManagerAware
from ranger.ext.safe_path import get_safe_path
from ranger.ext.signals import SignalDispatcher
from ranger.ext.human_readable import human_readable


class Loadable(object):
    paused = False
    progressbar_supported = False

    def __init__(self, gen, descr):
        self.load_generator = gen
        self.description = descr
        self.percent = 0

    def get_description(self):
        return self.description

    def pause(self):
        self.paused = True

    def unpause(self):
        try:
            del self.paused
        except AttributeError:
            pass

    def destroy(self):
        pass


class CopyLoader(Loadable, FileManagerAware):  # pylint: disable=too-many-instance-attributes
    progressbar_supported = True

    def __init__(self, copy_buffer, do_cut=False, overwrite=False, dest=None,
                 make_safe_path=get_safe_path):
        self.copy_buffer = tuple(copy_buffer)
        self.do_cut = do_cut
        self.original_copy_buffer = copy_buffer
        self.original_path = dest if dest is not None else self.fm.thistab.path
        self.overwrite = overwrite
        self.make_safe_path = make_safe_path
        self.percent = 0
        if self.copy_buffer:
            self.one_file = self.copy_buffer[0]
        Loadable.__init__(self, self.generate(), 'Calculating size...')

    def _calculate_size(self, step):
        from os.path import join
        size = 0
        stack = [fobj.path for fobj in self.copy_buffer]
        while stack:
            fname = stack.pop()
            if os.path.islink(fname):
                continue
            if os.path.isdir(fname):
                stack.extend([join(fname, item) for item in os.listdir(fname)])
            else:
                try:
                    fstat = os.stat(fname)
                except OSError:
                    continue
                size += max(step, math.ceil(fstat.st_size / step) * step)
        return size

    def generate(self):
        if not self.copy_buffer:
            return

        from ranger.ext import shutil_generatorized as shutil_g
        # TODO: Don't calculate size when renaming (needs detection)
        bytes_per_tick = shutil_g.BLOCK_SIZE
        size = max(1, self._calculate_size(bytes_per_tick))
        size_str = " (" + human_readable(self._calculate_size(1)) + ")"
        done = 0
        if self.do_cut:
            self.original_copy_buffer.clear()
            if len(self.copy_buffer) == 1:
                self.description = "moving: " + self.one_file.path + size_str
            else:
                self.description = "moving files from: " + self.one_file.dirname + size_str
            for fobj in self.copy_buffer:
                for path in self.fm.tags.tags:
                    if path == fobj.path or str(path).startswith(fobj.path):
                        tag = self.fm.tags.tags[path]
                        self.fm.tags.remove(path)
                        new_path = path.replace(
                            fobj.path,
                            os.path.join(self.original_path, fobj.basename))
                        self.fm.tags.tags[new_path] = tag
                        self.fm.tags.dump()
                n = 0
                for n in shutil_g.move(src=fobj.path, dst=self.original_path,
                                       overwrite=self.overwrite,
                                       make_safe_path=self.make_safe_path):
                    self.percent = ((done + n) / size) * 100.
                    yield
                done += n
        else:
            if len(self.copy_buffer) == 1:
                self.description = "copying: " + self.one_file.path + size_str
            else:
                self.description = "copying files from: " + self.one_file.dirname + size_str
            for fobj in self.copy_buffer:
                if os.path.isdir(fobj.path) and not os.path.islink(fobj.path):
                    n = 0
                    for n in shutil_g.copytree(
                            src=fobj.path,
                            dst=os.path.join(self.original_path, fobj.basename),
                            symlinks=True,
                            overwrite=self.overwrite,
                            make_safe_path=self.make_safe_path,
                    ):
                        self.percent = ((done + n) / size) * 100.
                        yield
                    done += n
                else:
                    n = 0
                    for n in shutil_g.copy2(fobj.path, self.original_path,
                                            symlinks=True, overwrite=self.overwrite,
                                            make_safe_path=self.make_safe_path):
                        self.percent = ((done + n) / size) * 100.
                        yield
                    done += n
        cwd = self.fm.get_directory(self.original_path)
        cwd.load_content()


class CommandLoader(  # pylint: disable=too-many-instance-attributes
        Loadable, SignalDispatcher, FileManagerAware):
    """Run an external command with the loader.

    Output from stderr will be reported.  Ensure that the process doesn't
    ever ask for input, otherwise the loader will be blocked until this
    object is removed from the queue (type ^C in ranger)
    """
    finished = False
    process = None

    def __init__(self, args, descr,  # pylint: disable=too-many-arguments
                 silent=False, read=False, input=None,  # pylint: disable=redefined-builtin
                 kill_on_pause=False, popenArgs=None):
        SignalDispatcher.__init__(self)
        Loadable.__init__(self, self.generate(), descr)
        self.args = args
        self.silent = silent
        self.read = read
        self.stdout_buffer = ""
        self.input = input
        self.kill_on_pause = kill_on_pause
        self.popenArgs = popenArgs  # pylint: disable=invalid-name

    def generate(self):  # pylint: disable=too-many-branches,too-many-statements
        popenargs = {} if self.popenArgs is None else self.popenArgs
        popenargs['stdout'] = popenargs['stderr'] = PIPE
        popenargs['stdin'] = PIPE if self.input else open(os.devnull, 'r')
        self.process = process = Popen(self.args, **popenargs)
        self.signal_emit('before', process=process, loader=self)
        if self.input:
            if PY3:
                import io
                stdin = io.TextIOWrapper(process.stdin)
            else:
                stdin = process.stdin
            try:
                stdin.write(self.input)
            except IOError as ex:
                if ex.errno != errno.EPIPE and ex.errno != errno.EINVAL:
                    raise
            stdin.close()
        if self.silent and not self.read:  # pylint: disable=too-many-nested-blocks
            while process.poll() is None:
                yield
                if self.finished:
                    break
                sleep(0.03)
        else:
            selectlist = []
            if self.read:
                selectlist.append(process.stdout)
            if not self.silent:
                selectlist.append(process.stderr)
            read_stdout = None
            while process.poll() is None:
                yield
                if self.finished:
                    break
                try:
                    robjs, _, _ = select.select(selectlist, [], [], 0.03)
                    if robjs:
                        robjs = robjs[0]
                        if robjs == process.stderr:
                            read = robjs.readline()
                            if PY3:
                                read = safe_decode(read)
                            if read:
                                self.fm.notify(read, bad=True)
                        elif robjs == process.stdout:
                            read = robjs.read(512)
                            if read:
                                if read_stdout is None:
                                    read_stdout = read
                                else:
                                    read_stdout += read
                except select.error:
                    sleep(0.03)
            if not self.silent:
                for line in process.stderr:
                    if PY3:
                        line = safe_decode(line)
                    self.fm.notify(line, bad=True)
            if self.read:
                read = process.stdout.read()
                if read:
                    read_stdout += read
            if read_stdout:
                if PY3:
                    read_stdout = safe_decode(read_stdout)
                self.stdout_buffer += read_stdout
        self.finished = True
        self.signal_emit('after', process=process, loader=self)

    def pause(self):
        if not self.finished and not self.paused:
            if self.kill_on_pause:
                self.finished = True
                try:
                    self.process.kill()
                except OSError:
                    # probably a race condition where the process finished
                    # between the last poll()ing and this point.
                    pass
                return
            try:
                self.process.send_signal(20)
            except OSError:
                pass
            Loadable.pause(self)
            self.signal_emit('pause', process=self.process, loader=self)

    def unpause(self):
        if not self.finished and self.paused:
            try:
                self.process.send_signal(18)
            except OSError:
                pass
            Loadable.unpause(self)
            self.signal_emit('unpause', process=self.process, loader=self)

    def destroy(self):
        self.signal_emit('destroy', process=self.process, loader=self)
        if self.process:
            try:
                self.process.kill()
            except OSError:
                pass


def safe_decode(string):
    try:
        return string.decode("utf-8")
    except UnicodeDecodeError:
        if HAVE_CHARDET:
            encoding = chardet.detect(string)["encoding"]
            if encoding:
                return string.decode(encoding, 'ignore')
        return ""


class Loader(FileManagerAware):
    """
    The Manager of 'Loadable' objects, referenced as fm.loader
    """
    seconds_of_work_time = 0.03
    throbber_chars = r'/-\|'
    throbber_paused = '#'
    paused = False

    def __init__(self):
        self.queue = deque()
        self.item = None
        self.load_generator = None
        self.throbber_status = 0
        self.rotate()
        self.old_item = None
        self.status = None

    def rotate(self):
        """Rotate the throbber"""
        # TODO: move all throbber logic to UI
        self.throbber_status = \
            (self.throbber_status + 1) % len(self.throbber_chars)
        self.status = self.throbber_chars[self.throbber_status]

    def add(self, obj, append=False):
        """Add an object to the queue.

        It should have a load_generator method.

        If the argument "append" is True, the queued object will be processed
        last, not first.
        """
        while obj in self.queue:
            self.queue.remove(obj)
        if append:
            self.queue.append(obj)
        else:
            self.queue.appendleft(obj)
        self.fm.signal_emit("loader.before", loadable=obj, fm=self.fm)
        if self.paused:
            obj.pause()
        else:
            obj.unpause()

    def move(self, pos_src, pos_dest):
        try:
            item = self.queue[pos_src]
        except IndexError:
            return

        del self.queue[pos_src]

        if pos_dest == 0:
            self.queue.appendleft(item)
            if pos_src != 0:
                self.queue[1].pause()
        elif pos_dest == -1:
            self.queue.append(item)
        else:
            raise NotImplementedError

    def remove(self, item=None, index=None):
        if item is not None and index is None:
            for i, test in enumerate(self.queue):
                if test == item:
                    index = i
                    break
            else:
                return

        if index is not None:
            if item is None:
                item = self.queue[index]
            if hasattr(item, 'unload'):
                item.unload()
            self.fm.signal_emit("loader.destroy", loadable=item, fm=self.fm)
            item.destroy()
            del self.queue[index]
            if item.progressbar_supported:
                self.fm.ui.status.request_redraw()

    def pause(self, state):
        """Change the pause-state to 1 (pause), 0 (no pause) or -1 (toggle)"""
        if state == -1:
            state = not self.paused
        elif state == self.paused:
            return

        self.paused = state

        if not self.queue:
            return

        if state:
            self.queue[0].pause()
        else:
            self.queue[0].unpause()

    def work(self):
        """Load items from the queue if there are any.

        Stop after approximately self.seconds_of_work_time.
        """
        if self.paused:
            self.status = self.throbber_paused
            return

        while True:
            # get the first item with a proper load_generator
            try:
                item = self.queue[0]
                if item.load_generator is None:
                    self.queue.popleft()
                else:
                    break
            except IndexError:
                return

        item.unpause()

        self.rotate()
        if item != self.old_item:
            if self.old_item:
                self.old_item.pause()
            self.old_item = item
        item.unpause()

        end_time = time() + self.seconds_of_work_time

        while time() < end_time:
            try:
                next(item.load_generator)
            except StopIteration:
                self._remove_current_process(item)
                break
            except Exception as ex:  # pylint: disable=broad-except
                self.fm.notify(
                    'Loader work process failed: {0} (Percent: {1})'.format(
                        item.description, item.percent),
                    bad=True,
                    exception=ex,
                )
                self.old_item = None
                self._remove_current_process(item)
                break
        else:
            if item.progressbar_supported:
                self.fm.ui.status.request_redraw()

    def _remove_current_process(self, item):
        item.load_generator = None
        self.queue.remove(item)
        self.fm.signal_emit("loader.after", loadable=item, fm=self.fm)
        if item.progressbar_supported:
            self.fm.ui.status.request_redraw()

    def has_work(self):
        """Is there anything to load?"""
        return bool(self.queue)

    def destroy(self):
        while self.queue:
            self.queue.pop().destroy()
