# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# Author: Emanuel Guevel, 2013
# Author: Delisa Mason, 2015

"""Interface for drawing images into the console

This module provides functions to draw images in the terminal using supported
implementations, which are currently w3m, iTerm2 and urxvt.
"""

import base64
import curses
import errno
import fcntl
import imghdr
import os
import select
import struct
import sys
import termios
from ranger.core.shared import FileManagerAware
from subprocess import Popen, PIPE
import subprocess
import json
import atexit
import socket
from pathlib import Path
import logging
from logging import info
import traceback
import shutil
from shutil import which

cache = Path(os.environ.get("XDG_CACHE_HOME", "~/.cache")).expanduser()
cache = cache / "ranger"
cache.mkdir(exist_ok=True)
logging.basicConfig(filename=str(cache / 'debug.log'), level=logging.INFO)

def _is_term(term):
    try:
        import psutil
    except ImportError:
        return False
    proc = psutil.Process()
    while proc:
        proc = proc.parent()
        if proc.name() == term:
            return True
    return False

image_displayers = {}
def register_image_displayer(nickname=None):
    """Register an ImageDisplayer by nickname if available."""
    def decorator(cls):
        image_displayers[nickname or cls.__name__] = cls
        return cls
    return decorator

class ImageDisplayer(object):
    """Provide functions for drawing images in the terminal"""

    def check(self):
        """Guess if this ImageDisplayer will run."""
        return False # pessimistic by default
        #  raise NotImplemented

    def draw(self, path, start_x, start_y, width, height):
        """Draw an image at the given coordinates."""
        pass

    def clear(self, start_x, start_y, width, height):
        """Clear a part of terminal display."""
        pass

    def quit(self):
        """Cleanup and close"""
        pass

class ImgDisplayUnsupportedException(Exception):
    pass

@register_image_displayer("auto")
def AutoImageDisplayer():
    """Automatically select a context-appropriate ImageDisplayer."""

    try_order = [
        ITerm2ImageDisplayer,
        URXVTImageDisplayer,
        #  MPVImageDisplayer,
        W3MImageDisplayer,
        #  ImageDisplayer,
        #  ASCIIImageDisplayer,
        ]

    for displayer in try_order:
        if displayer.check():
            return displayer()

    raise ImgDisplayUnsupportedException
    #  raise NoImageDisplayerFound

def _ignore_errors(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except:
        pass

@register_image_displayer("mpv")
class MPVImageDisplayer(ImageDisplayer):
    """Implementation of ImageDisplayer using mpv, a general media viewer.
    Opens media in a separate X window.

    mpv need to be installed for this to work.
    """

    def check(self):
        if os.environ.get('DISPLAY', None):
            return shutil.which('mpv')

    def _send_command(self, path, sock):

        message = '{"command": ["raw","loadfile",%s]}\n' % json.dumps(path)
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(str(sock))
        #  info('-> ' + message)
        s.send(message.encode())
        message = s.recv(1024).decode()
        #  info('<- ' + message)
        s.close()

    def _launch_mpv(self, path, sock):

        proc = Popen([
            * os.environ.get("MPV", "mpv").split(),
            "--no-terminal",
            #  "--force-window",
            "--input-ipc-server=" + str(sock),
            "--image-display-duration=inf",
            "--loop-file=inf",
            "--no-osc",
            "--no-input-default-bindings",
            #  "--no-input-cursor",
            "--keep-open",
            "--idle",

            # actually fix the window resizing problem
            "--geometry=600x400",  # fixed aspect ratio
            "--no-keepaspect-window",

            # attempts to fix window resizing problem
            #  "--geometry=600x400",  # fixed aspect ratio
            #  "--geometry=600",      # fixes width
            #  "--geometry",      # nope,  breaks
            #  "--fixed-vo",
            #  "--force-window-position", # nope
            #  "--video-unscaled=yes", # nope
            "--",
            path,
        ])

        @atexit.register
        def cleanup():
            _ignore_errors(proc.terminate)
            _ignore_errors(sock.unlink)

    def draw(self, path, start_x, start_y, width, height):

        path = os.path.abspath(path)
        sock = cache / "image-slave.sock"

        try:
            self._send_command(path, sock)
        except (ConnectionRefusedError, FileNotFoundError):
            #  info('LAUNCHING ' + path)
            self._launch_mpv(path, sock)
        #  except Exception as e:
        #      logging.exception(traceback.format_exc())
        #      sys.exit(1)
        #  info('SUCCESS')

@register_image_displayer("w3m")
class W3MImageDisplayer(ImageDisplayer):
    """Implementation of ImageDisplayer using w3mimgdisplay, an utilitary
    program from w3m (a text-based web browser). w3mimgdisplay can display
    images either in virtual tty (using linux framebuffer) or in a Xorg session.
    Does not work over ssh.

    w3m need to be installed for this to work.
    """
    is_initialized = False

    W3MIMGDISPLAY_ENV = "W3MIMGDISPLAY_PATH"
    W3MIMGDISPLAY_OPTIONS = []
    W3MIMGDISPLAY_PATHS = [
        '/usr/lib/w3m/w3mimgdisplay',
        '/usr/libexec/w3m/w3mimgdisplay',
        '/usr/lib64/w3m/w3mimgdisplay',
        '/usr/libexec64/w3m/w3mimgdisplay',
    ]

    def check(self):
        return any(os.path.exists(path) for path in W3MIMGDISPLAY_PATHS)

    def initialize(self):
        """start w3mimgdisplay"""
        self.binary_path = None
        self.binary_path = self._find_w3mimgdisplay_executable()  # may crash
        self.process = Popen([self.binary_path] + W3MIMGDISPLAY_OPTIONS,
                stdin=PIPE, stdout=PIPE, universal_newlines=True)
        self.is_initialized = True

    def _find_w3mimgdisplay_executable(self):
        paths = [os.environ.get(W3MIMGDISPLAY_ENV, None)] + W3MIMGDISPLAY_PATHS
        for path in paths:
            if path is not None and os.path.exists(path):
                return path
        raise RuntimeError("No w3mimgdisplay executable found.  Please set "
            "the path manually by setting the %s environment variable.  (see "
            "man page)" % W3MIMGDISPLAY_ENV)

    def _get_font_dimensions(self):
        # Get the height and width of a character displayed in the terminal in
        # pixels.
        if self.binary_path is None:
            self.binary_path = self._find_w3mimgdisplay_executable()
        s = struct.pack("HHHH", 0, 0, 0, 0)
        fd_stdout = sys.stdout.fileno()
        x = fcntl.ioctl(fd_stdout, termios.TIOCGWINSZ, s)
        rows, cols, xpixels, ypixels = struct.unpack("HHHH", x)
        if xpixels == 0 and ypixels == 0:
            process = Popen([self.binary_path, "-test"],
                stdout=PIPE, universal_newlines=True)
            output, _ = process.communicate()
            output = output.split()
            xpixels, ypixels = int(output[0]), int(output[1])
            # adjust for misplacement
            xpixels += 2
            ypixels += 2

        return (xpixels // cols), (ypixels // rows)

    def draw(self, path, start_x, start_y, width, height):
        if not self.is_initialized or self.process.poll() is not None:
            self.initialize()
        self.process.stdin.write(self._generate_w3m_input(path, start_x,
            start_y, width, height))
        self.process.stdin.flush()
        self.process.stdout.readline()

    def clear(self, start_x, start_y, width, height):
        if not self.is_initialized or self.process.poll() is not None:
            self.initialize()

        fontw, fonth = self._get_font_dimensions()

        cmd = "6;{x};{y};{w};{h}\n4;\n3;\n".format(
                x=int((start_x - 0.2) * fontw),
                y=start_y * fonth,
                # y = int((start_y + 1) * fonth), # (for tmux top status bar)
                w=int((width + 0.4) * fontw),
                h=height * fonth + 1)
                # h = (height - 1) * fonth + 1) # (for tmux top status bar)

        try:
            self.process.stdin.write(cmd)
        except IOError as e:
            if e.errno == errno.EPIPE:
                return
            else:
                raise e
        self.process.stdin.flush()
        self.process.stdout.readline()

    def _generate_w3m_input(self, path, start_x, start_y, max_width, max_height):
        """Prepare the input string for w3mimgpreview

        start_x, start_y, max_height and max_width specify the drawing area.
        They are expressed in number of characters.
        """
        fontw, fonth = self._get_font_dimensions()
        if fontw == 0 or fonth == 0:
            raise ImgDisplayUnsupportedException()

        max_width_pixels = max_width * fontw
        max_height_pixels = max_height * fonth - 2
        # (for tmux top status bar)
        # max_height_pixels = (max_height - 1) * fonth - 2

        # get image size
        cmd = "5;{}\n".format(path)

        self.process.stdin.write(cmd)
        self.process.stdin.flush()
        output = self.process.stdout.readline().split()

        if len(output) != 2:
            raise Exception('Failed to execute w3mimgdisplay', output)

        width = int(output[0])
        height = int(output[1])

        # get the maximum image size preserving ratio
        if width > max_width_pixels:
            height = (height * max_width_pixels) // width
            width = max_width_pixels
        if height > max_height_pixels:
            width = (width * max_height_pixels) // height
            height = max_height_pixels

        return "0;1;{x};{y};{w};{h};;;;;{filename}\n4;\n3;\n".format(
                x=int((start_x - 0.2) * fontw),
                y=start_y * fonth,
                # y = (start_y + 1) * fonth, # (for tmux top status bar)
                w=width,
                h=height,
                filename=path)

    def quit(self):
        if self.is_initialized and self.process and self.process.poll() is None:
            self.process.kill()

# TODO: remove FileManagerAwareness, as stuff in ranger.ext should be
# ranger-independent libraries.


@register_image_displayer("iterm2")
class ITerm2ImageDisplayer(ImageDisplayer, FileManagerAware):
    """Implementation of ImageDisplayer using iTerm2 image display support
    (http://iterm2.com/images.html).

    Ranger must be running in iTerm2 for this to work.
    """

    _minimum_font_width = 8
    _minimum_font_height = 11

    def check(self):
        # Is the name of the binary iterm or iterm2?
        return _is_term("iterm2")
        #  return os.environ.get('TERM', '').startswith('iterm2')
        # TERM value?
        # EXE name?

    def draw(self, path, start_x, start_y, width, height):
        curses.putp(curses.tigetstr("sc"))
        sys.stdout.write(curses.tparm(curses.tigetstr("cup"), start_y, start_x))
        sys.stdout.write(self._generate_iterm2_input(path, width, height))
        curses.putp(curses.tigetstr("rc"))
        sys.stdout.flush()

    def clear(self, start_x, start_y, width, height):
        self.fm.ui.win.redrawwin()
        self.fm.ui.win.refresh()

    def _generate_iterm2_input(self, path, max_cols, max_rows):
        """Prepare the image content of path for image display in iTerm2"""
        image_width, image_height = self._get_image_dimensions(path)
        if max_cols == 0 or max_rows == 0 or image_width == 0 or image_height == 0:
            return ""
        image_width = self._fit_width(
            image_width, image_height, max_cols, max_rows)
        content = self._encode_image_content(path)
        display_protocol = "\033"
        close_protocol = "\a"
        if "screen" in os.environ['TERM']:
            display_protocol += "Ptmux;\033\033"
            close_protocol += "\033\\"

        text = "{0}]1337;File=inline=1;preserveAspectRatio=0;size={1};width={2}px:{3}{4}\n".format(
            display_protocol,
            str(len(content)),
            str(int(image_width)),
            content,
            close_protocol)
        return text

    def _fit_width(self, width, height, max_cols, max_rows):
        max_width = self._minimum_font_width * max_cols
        max_height = self._minimum_font_height * max_rows
        if height > max_height:
            if width > max_width:
                width_scale = max_width / float(width)
                height_scale = max_height / float(height)
                min_scale = min(width_scale, height_scale)
                max_scale = max(width_scale, height_scale)
                if width * max_scale <= max_width and height * max_scale <= max_height:
                    return (width * max_scale)
                else:
                    return (width * min_scale)
            else:
                scale = max_height / float(height)
                return (width * scale)
        elif width > max_width:
            scale = max_width / float(width)
            return (width * scale)
        else:
            return width

    def _encode_image_content(self, path):
        """Read and encode the contents of path"""
        file = open(path, 'rb')
        try:
            return base64.b64encode(file.read())
        except Exception:
            return ""
        finally:
            file.close()

    def _get_image_dimensions(self, path):
        """Determine image size using imghdr"""
        file_handle = open(path, 'rb')
        file_header = file_handle.read(24)
        image_type  = imghdr.what(path)
        if len(file_header) != 24:
            file_handle.close()
            return 0, 0
        if image_type == 'png':
            check = struct.unpack('>i', file_header[4:8])[0]
            if check != 0x0d0a1a0a:
                file_handle.close()
                return 0, 0
            width, height = struct.unpack('>ii', file_header[16:24])
        elif image_type == 'gif':
            width, height = struct.unpack('<HH', file_header[6:10])
        elif image_type == 'jpeg':
            try:
                file_handle.seek(0)
                size = 2
                ftype = 0
                while not 0xc0 <= ftype <= 0xcf:
                    file_handle.seek(size, 1)
                    byte = file_handle.read(1)
                    while ord(byte) == 0xff:
                        byte = file_handle.read(1)
                    ftype = ord(byte)
                    size = struct.unpack('>H', file_handle.read(2))[0] - 2
                file_handle.seek(1, 1)
                height, width = struct.unpack('>HH', file_handle.read(4))
            except Exception:
                file_handle.close()
                return 0, 0
        else:
            file_handle.close()
            return 0, 0
        file_handle.close()
        return width, height


@register_image_displayer("urxvt")
class URXVTImageDisplayer(ImageDisplayer, FileManagerAware):
    """Implementation of ImageDisplayer working by setting the urxvt
    background image "under" the preview pane.

    Ranger must be running in urxvt for this to work.

    """

    def check(self):
        return os.environ.get('TERM', '').startswith('urxvt')

    def _get_max_sizes(self):
        """Use the whole terminal."""
        w = 100
        h = 100
        return w, h

    def _get_centered_offsets(self):
        """Center the image."""
        x = 50
        y = 50
        return x, y

    def _get_sizes(self):
        """Return the width and height of the preview pane in relation to the
        whole terminal window.

        """
        if self.fm.ui.pager.visible:
            return self._get_max_sizes()

        total_columns_ratio = sum(self.fm.settings.column_ratios)
        preview_column_ratio = self.fm.settings.column_ratios[-1]
        w = int((100 * preview_column_ratio) / total_columns_ratio)
        h = 100  # As much as possible while preserving the aspect ratio.
        return w, h

    def _get_offsets(self):
        """Return the offsets of the image center."""
        if self.fm.ui.pager.visible:
            return self._get_centered_offsets()

        x = 100  # Right-aligned.
        y = 2    # TODO: Use the font size to calculate this offset.
        return x, y

    def draw(self, path, start_x, start_y, width, height):
        # The coordinates in the arguments are ignored as urxvt takes
        # the coordinates in a non-standard way: the position of the
        # image center as a percentage of the terminal size. As a
        # result all values below are in percents.

        x, y = self._get_offsets()
        w, h = self._get_sizes()

        sys.stdout.write("\033]20;{path};{w}x{h}+{x}+{y}:op=keep-aspect\a".format(**vars()))
        sys.stdout.flush()

    def clear(self, start_x, start_y, width, height):
        sys.stdout.write("\033]20;;100x100+1000+1000\a")
        sys.stdout.flush()

    def quit(self):
        sys.stdout.write("\033]20;;100x100+1000+1000\a")
        sys.stdout.flush()


@register_image_displayer("urxvt-full")
class URXVTImageFSDisplayer(URXVTImageDisplayer):
    """URXVTImageDisplayer that utilizes the whole terminal."""

    def _get_sizes(self):
        """Use the whole terminal."""
        return self._get_max_sizes()

    def _get_offsets(self):
        """Center the image."""
        return self._get_centered_offsets()
