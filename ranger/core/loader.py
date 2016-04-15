# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from collections import deque
from time import time, sleep
from subprocess import Popen, PIPE
from ranger.core.shared import FileManagerAware
from ranger.ext.signals import SignalDispatcher
from ranger.ext.human_readable import human_readable
import math
import os.path
import sys
import select
try:
    import chardet
    HAVE_CHARDET = True
except:
    HAVE_CHARDET = False

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
        except:
            pass

    def destroy(self):
        pass


class CopyLoader(Loadable, FileManagerAware):
    progressbar_supported = True
    def __init__(self, copy_buffer, do_cut=False, overwrite=False):
        self.copy_buffer = tuple(copy_buffer)
        self.do_cut = do_cut
        self.original_copy_buffer = copy_buffer
        self.original_path = self.fm.thistab.path
        self.overwrite = overwrite
        self.percent = 0
        if self.copy_buffer:
            self.one_file = self.copy_buffer[0]
        Loadable.__init__(self, self.generate(), 'Calculating size...')

    def _calculate_size(self, step):
        from os.path import join
        size = 0
        stack = [f.path for f in self.copy_buffer]
        while stack:
            fname = stack.pop()
            if os.path.islink(fname):
                continue
            if os.path.isdir(fname):
                stack.extend([join(fname, item) for item in os.listdir(fname)])
            else:
                try:
                    fstat = os.stat(fname)
                except:
                    continue
                size += max(step, math.ceil(fstat.st_size / step) * step)
        return size

    def generate(self):
        from ranger.ext import shutil_generatorized as shutil_g
        if self.copy_buffer:
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
                for f in self.copy_buffer:
                    for tf in self.fm.tags.tags:
                        if tf == f.path or str(tf).startswith(f.path):
                            tag = self.fm.tags.tags[tf]
                            self.fm.tags.remove(tf)
                            self.fm.tags.tags[tf.replace(f.path, self.original_path \
                                    + '/' + f.basename)] = tag
                            self.fm.tags.dump()
                    d = 0
                    for d in shutil_g.move(src=f.path,
                            dst=self.original_path,
                            overwrite=self.overwrite):
                        self.percent = float(done + d) / size * 100.
                        yield
                    done += d
            else:
                if len(self.copy_buffer) == 1:
                    self.description = "copying: " + self.one_file.path + size_str
                else:
                    self.description = "copying files from: " + self.one_file.dirname + size_str
                for f in self.copy_buffer:
                    if os.path.isdir(f.path) and not os.path.islink(f.path):
                        d = 0
                        for d in shutil_g.copytree(src=f.path,
                                dst=os.path.join(self.original_path, f.basename),
                                symlinks=True,
                                overwrite=self.overwrite):
                            self.percent = float(done + d) / size * 100.
                            yield
                        done += d
                    else:
                        d = 0
                        for d in shutil_g.copy2(f.path, self.original_path,
                                symlinks=True,
                                overwrite=self.overwrite):
                            self.percent = float(done + d) / size * 100.
                            yield
                        done += d
            cwd = self.fm.get_directory(self.original_path)
            cwd.load_content()


class CommandLoader(Loadable, SignalDispatcher, FileManagerAware):
    """Run an external command with the loader.

    Output from stderr will be reported.  Ensure that the process doesn't
    ever ask for input, otherwise the loader will be blocked until this
    object is removed from the queue (type ^C in ranger)
    """
    finished = False
    process = None
    def __init__(self, args, descr, silent=False, read=False, input=None,
            kill_on_pause=False, popenArgs=None):
        SignalDispatcher.__init__(self)
        Loadable.__init__(self, self.generate(), descr)
        self.args = args
        self.silent = silent
        self.read = read
        self.stdout_buffer = ""
        self.input = input
        self.kill_on_pause = kill_on_pause
        self.popenArgs = popenArgs

    def generate(self):
        py3 = sys.version_info[0] >= 3
        if self.input:
            stdin = PIPE
        else:
            stdin = open(os.devnull, 'r')
        popenArgs = {} if self.popenArgs is None else self.popenArgs
        popenArgs['stdout'] = popenArgs['stderr'] = PIPE
        popenArgs['stdin'] = stdin
        self.process = process = Popen(self.args, **popenArgs)
        self.signal_emit('before', process=process, loader=self)
        if self.input:
            if py3:
                import io
                stdin = io.TextIOWrapper(process.stdin)
            else:
                stdin = process.stdin
            try:
                stdin.write(self.input)
            except IOError as e:
                if e.errno != errno.EPIPE and e.errno != errno.EINVAL:
                    raise
            stdin.close()
        if self.silent and not self.read:
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
            while process.poll() is None:
                yield
                if self.finished:
                    break
                try:
                    rd, _, __ = select.select(selectlist, [], [], 0.03)
                    if rd:
                        rd = rd[0]
                        if rd == process.stderr:
                            read = rd.readline()
                            if py3:
                                read = safeDecode(read)
                            if read:
                                self.fm.notify(read, bad=True)
                        elif rd == process.stdout:
                            read = rd.read(512)
                            if py3:
                                read = safeDecode(read)
                            if read:
                                self.stdout_buffer += read
                except select.error:
                    sleep(0.03)
            if not self.silent:
                for l in process.stderr.readlines():
                    if py3:
                        l = safeDecode(l)
                    self.fm.notify(l, bad=True)
            if self.read:
                read = process.stdout.read()
                if py3:
                    read = safeDecode(read)
                self.stdout_buffer += read
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
            except:
                pass
            Loadable.pause(self)
            self.signal_emit('pause', process=self.process, loader=self)

    def unpause(self):
        if not self.finished and self.paused:
            try:
                self.process.send_signal(18)
            except:
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


def safeDecode(string):
    try:
        return string.decode("utf-8")
    except (UnicodeDecodeError):
        if HAVE_CHARDET:
            codec = chardet.detect(string)["encoding"]
            return string.decode(codec, 'ignore')
        else:
            return ""


class Loader(FileManagerAware):
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
        if self.paused:
            obj.pause()
        else:
            obj.unpause()

    def move(self, _from, to):
        try:
            item = self.queue[_from]
        except IndexError:
            return

        del self.queue[_from]

        if to == 0:
            self.queue.appendleft(item)
            if _from != 0:
                self.queue[1].pause()
        elif to == -1:
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

        try:
            while time() < end_time:
                next(item.load_generator)
            if item.progressbar_supported:
                self.fm.ui.status.request_redraw()
        except StopIteration:
            self._remove_current_process(item)
        except Exception as err:
            self.fm.notify(err)
            self._remove_current_process(item)

    def _remove_current_process(self, item):
        item.load_generator = None
        self.queue.remove(item)
        if item.progressbar_supported:
            self.fm.ui.status.request_redraw()

    def has_work(self):
        """Is there anything to load?"""
        return bool(self.queue)

    def destroy(self):
        while self.queue:
            self.queue.pop().destroy()
