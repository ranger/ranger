# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# Author: Emanuel Guevel, 2013
# Author: Delisa Mason, 2015

"""Interface for drawing images into the console

This module provides functions to draw images in the terminal using supported
implementations.
"""

from __future__ import (absolute_import, division, print_function)

import base64
import curses
import errno
import fcntl
import os
import struct
import sys
import warnings
import json
import mmap
import threading
from subprocess import Popen, PIPE, check_call, CalledProcessError
from collections import defaultdict, namedtuple

import termios
from contextlib import contextmanager
import codecs
from tempfile import gettempdir, NamedTemporaryFile, TemporaryFile

from ranger import PY3
from ranger.core.shared import FileManagerAware, SettingsAware
from ranger.ext.popen23 import Popen23, DEVNULL
from ranger.ext.which import which


if which("magick"):
    # Magick >= 7
    MAGICK_CONVERT_CMD_BASE = ("magick",)
else:
    # Magick < 7
    MAGICK_CONVERT_CMD_BASE = ("convert",)


W3MIMGDISPLAY_ENV = "W3MIMGDISPLAY_PATH"
W3MIMGDISPLAY_OPTIONS = []
W3MIMGDISPLAY_PATHS = [
    '/usr/lib/w3m/w3mimgdisplay',
    '/usr/libexec/w3m/w3mimgdisplay',
    '/usr/lib64/w3m/w3mimgdisplay',
    '/usr/libexec64/w3m/w3mimgdisplay',
    '/usr/local/libexec/w3m/w3mimgdisplay',
]

# Helper functions shared between the previewers (make them static methods of the base class?)


@contextmanager
def temporarily_moved_cursor(to_y, to_x):
    """Common boilerplate code to move the cursor to a drawing area. Use it as:
        with temporarily_moved_cursor(dest_y, dest_x):
            your_func_here()"""
    curses.putp(curses.tigetstr("sc"))
    move_cur(to_y, to_x)
    yield
    curses.putp(curses.tigetstr("rc"))
    sys.stdout.flush()


# this is excised since Terminology needs to move the cursor multiple times
def move_cur(to_y, to_x):
    tparm = curses.tparm(curses.tigetstr("cup"), to_y, to_x)
    # on python2 stdout is already in binary mode, in python3 is accessed via buffer
    bin_stdout = getattr(sys.stdout, 'buffer', sys.stdout)
    bin_stdout.write(tparm)


def get_terminal_size():
    farg = struct.pack("HHHH", 0, 0, 0, 0)
    fd_stdout = sys.stdout.fileno()
    fretint = fcntl.ioctl(fd_stdout, termios.TIOCGWINSZ, farg)
    return struct.unpack("HHHH", fretint)


def get_font_dimensions():
    """
    Get the height and width of a character displayed in the terminal in
    pixels.
    """
    rows, cols, xpixels, ypixels = get_terminal_size()
    return (xpixels // cols), (ypixels // rows)


def image_fit_width(width, height, max_cols, max_rows, font_width=None, font_height=None):
    if font_width is None or font_height is None:
        font_width, font_height = get_font_dimensions()

    max_width = font_width * max_cols
    max_height = font_height * max_rows
    if height > max_height:
        if width > max_width:
            width_scale = max_width / width
            height_scale = max_height / height
            min_scale = min(width_scale, height_scale)
            return width * min_scale
        else:
            scale = max_height / height
            return width * scale
    elif width > max_width:
        scale = max_width / width
        return width * scale
    else:
        return width


class ImageDisplayError(Exception):
    pass


class ImgDisplayUnsupportedException(Exception, SettingsAware):
    def __init__(self, message=None):
        if message is None:
            message = (
                '"{0}" does not appear to be a valid setting for'
                ' preview_images_method.'
            ).format(self.settings.preview_images_method)
        super(ImgDisplayUnsupportedException, self).__init__(message)


def fallback_image_displayer():
    """Simply makes some noise when chosen. Temporary fallback behavior."""

    raise ImgDisplayUnsupportedException


IMAGE_DISPLAYER_REGISTRY = defaultdict(fallback_image_displayer)


def register_image_displayer(nickname=None):
    """Register an ImageDisplayer by nickname if available."""

    def decorator(image_displayer_class):
        if nickname:
            registry_key = nickname
        else:
            registry_key = image_displayer_class.__name__
        IMAGE_DISPLAYER_REGISTRY[registry_key] = image_displayer_class
        return image_displayer_class
    return decorator


def get_image_displayer(registry_key):
    image_displayer_class = IMAGE_DISPLAYER_REGISTRY[registry_key]
    return image_displayer_class()


class ImageDisplayer(object):
    """Image display provider functions for drawing images in the terminal"""

    working_dir = os.environ.get('XDG_RUNTIME_DIR', os.path.expanduser("~") or None)

    def draw(self, path, start_x, start_y, width, height):
        """Draw an image at the given coordinates."""

    def clear(self, start_x, start_y, width, height):
        """Clear a part of terminal display."""

    def quit(self):
        """Cleanup and close"""


@register_image_displayer("w3m")
class W3MImageDisplayer(ImageDisplayer, FileManagerAware):
    """Implementation of ImageDisplayer using w3mimgdisplay, an utilitary
    program from w3m (a text-based web browser). w3mimgdisplay can display
    images either in virtual tty (using linux framebuffer) or in a Xorg session.
    Does not work over ssh.

    w3m need to be installed for this to work.
    """
    is_initialized = False

    def __init__(self):
        self.binary_path = None
        self.process = None

    def initialize(self):
        """start w3mimgdisplay"""
        self.binary_path = None
        self.binary_path = self._find_w3mimgdisplay_executable()  # may crash
        # We cannot close the process because that stops the preview.
        # pylint: disable=consider-using-with
        self.process = Popen([self.binary_path] + W3MIMGDISPLAY_OPTIONS, cwd=self.working_dir,
                             stdin=PIPE, stdout=PIPE, universal_newlines=True)
        self.is_initialized = True

    @staticmethod
    def _find_w3mimgdisplay_executable():
        paths = [os.environ.get(W3MIMGDISPLAY_ENV, None)] + W3MIMGDISPLAY_PATHS
        for path in paths:
            if path is not None and os.path.exists(path):
                return path
        raise ImageDisplayError("No w3mimgdisplay executable found.  Please set "
                                "the path manually by setting the %s environment variable.  (see "
                                "man page)" % W3MIMGDISPLAY_ENV)

    def _get_font_dimensions(self):
        # Get the height and width of a character displayed in the terminal in
        # pixels.
        if self.binary_path is None:
            self.binary_path = self._find_w3mimgdisplay_executable()
        farg = struct.pack("HHHH", 0, 0, 0, 0)
        fd_stdout = sys.stdout.fileno()
        fretint = fcntl.ioctl(fd_stdout, termios.TIOCGWINSZ, farg)
        rows, cols, xpixels, ypixels = struct.unpack("HHHH", fretint)
        if xpixels == 0 and ypixels == 0:
            with Popen23(
                [self.binary_path, "-test"],
                stdout=PIPE,
                universal_newlines=True,
            ) as process:
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
        input_gen = self._generate_w3m_input(path, start_x, start_y, width,
                                             height)
        self.process.stdin.write(input_gen)
        self.process.stdin.flush()
        self.process.stdout.readline()

        # Mitigate the issue with the horizontal black bars when
        # selecting some images on some systems. 2 milliseconds seems
        # enough. Adjust as necessary.
        if self.fm.settings.w3m_delay > 0:
            from time import sleep
            sleep(self.fm.settings.w3m_delay)

        # HACK workaround for w3mimgdisplay memory leak
        self.quit()
        self.is_initialized = False

    def clear(self, start_x, start_y, width, height):
        if not self.is_initialized or self.process.poll() is not None:
            self.initialize()

        fontw, fonth = self._get_font_dimensions()

        cmd = "6;{x};{y};{w};{h}\n4;\n3;\n".format(
            x=int((start_x - 0.2) * fontw),
            y=start_y * fonth,
            # y = int((start_y + 1) * fonth), # (for tmux top status bar)
            w=int((width + 0.4) * fontw),
            h=height * fonth + 1,
            # h = (height - 1) * fonth + 1, # (for tmux top status bar)
        )

        try:
            self.fm.ui.win.redrawwin()
            self.process.stdin.write(cmd)
        except IOError as ex:
            if ex.errno == errno.EPIPE:
                return
            raise
        self.process.stdin.flush()
        self.process.stdout.readline()

    def _generate_w3m_input(self, path, start_x, start_y, max_width, max_height):
        """Prepare the input string for w3mimgpreview

        start_x, start_y, max_height and max_width specify the drawing area.
        They are expressed in number of characters.
        """
        fontw, fonth = self._get_font_dimensions()
        if fontw == 0 or fonth == 0:
            raise ImgDisplayUnsupportedException

        max_width_pixels = max_width * fontw
        max_height_pixels = max_height * fonth - 2
        # (for tmux top status bar)
        # max_height_pixels = (max_height - 1) * fonth - 2

        # get image size
        cmd = "5;{path}\n".format(path=path)

        self.process.stdin.write(cmd)
        self.process.stdin.flush()
        output = self.process.stdout.readline().split()

        if len(output) != 2:
            raise ImageDisplayError('Failed to execute w3mimgdisplay', output)

        width = int(output[0])
        height = int(output[1])

        # get the maximum image size preserving ratio
        if width > max_width_pixels:
            height = (height * max_width_pixels) // width
            width = max_width_pixels
        if height > max_height_pixels:
            width = (width * max_height_pixels) // height
            height = max_height_pixels

        start_x = int((start_x - 0.2) * fontw) + self.fm.settings.w3m_offset
        start_y = (start_y * fonth) + self.fm.settings.w3m_offset

        return "0;1;{x};{y};{w};{h};;;;;{filename}\n4;\n3;\n".format(
            x=start_x,
            y=start_y,
            # y = (start_y + 1) * fonth, # (for tmux top status bar)
            w=width,
            h=height,
            filename=path,
        )

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

    def draw(self, path, start_x, start_y, width, height):
        with temporarily_moved_cursor(start_y, start_x):
            sys.stdout.write(self._generate_iterm2_input(path, width, height))

    def clear(self, start_x, start_y, width, height):
        self.fm.ui.win.redrawwin()
        self.fm.ui.win.refresh()

    def quit(self):
        self.clear(0, 0, 0, 0)

    def _generate_iterm2_input(self, path, max_cols, max_rows):
        """Prepare the image content of path for image display in iTerm2"""
        image_width, image_height = self._get_image_dimensions(path)
        if max_cols == 0 or max_rows == 0 or image_width == 0 or image_height == 0:
            return ""
        image_width = self._fit_width(
            image_width, image_height, max_cols, max_rows)
        content, byte_size = self._encode_image_content(path)
        display_protocol = "\033"
        close_protocol = "\a"
        if os.environ["TERM"].startswith(("screen", "tmux")):
            display_protocol += "Ptmux;\033\033"
            close_protocol += "\033\\"

        text = "{0}]1337;File=inline=1;preserveAspectRatio=0;size={1};width={2}px:{3}{4}\n".format(
            display_protocol,
            str(byte_size),
            str(int(image_width)),
            content,
            close_protocol)
        return text

    def _fit_width(self, width, height, max_cols, max_rows):
        font_width = self.fm.settings.iterm2_font_width
        font_height = self.fm.settings.iterm2_font_height

        return image_fit_width(
            width, height, max_cols, max_rows, font_width, font_height
        )

    @staticmethod
    def _encode_image_content(path):
        """Read and encode the contents of path"""
        with open(path, 'rb') as fobj:
            content = fobj.read()
            return base64.b64encode(content).decode('utf-8'), len(content)

    @staticmethod
    def imghdr_what(path):
        """Replacement for the deprecated imghdr module"""
        with open(path, "rb") as img_file:
            header = img_file.read(32)
            if header[6:10] in (b'JFIF', b'Exif'):
                return 'jpeg'
            elif header[:4] == b'\xff\xd8\xff\xdb':
                return 'jpeg'
            elif header.startswith(b'\211PNG\r\n\032\n'):
                return 'png'
            if header[:6] in (b'GIF87a', b'GIF89a'):
                return 'gif'
            else:
                return None

    @staticmethod
    def _get_image_dimensions(path):
        """Determine image size using imghdr"""
        with open(path, 'rb') as file_handle:
            file_header = file_handle.read(24)
            image_type = ITerm2ImageDisplayer.imghdr_what(path)
            if len(file_header) != 24:
                return 0, 0
            if image_type == 'png':
                check = struct.unpack('>i', file_header[4:8])[0]
                if check != 0x0d0a1a0a:
                    return 0, 0
                width, height = struct.unpack('>ii', file_header[16:24])
            elif image_type == 'gif':
                width, height = struct.unpack('<HH', file_header[6:10])
            elif image_type == 'jpeg':
                unreadable = OSError if PY3 else IOError
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
                except unreadable:
                    height, width = 0, 0
            else:
                return 0, 0
        return width, height


_CacheableSixelImage = namedtuple("_CacheableSixelImage", ("width", "height", "inode"))

_CachedSixelImage = namedtuple("_CachedSixelImage", ("image", "fh"))


@register_image_displayer("sixel")
class SixelImageDisplayer(ImageDisplayer, FileManagerAware):
    """Implementation of ImageDisplayer using SIXEL."""

    def __init__(self):
        self.win = None
        self.cache = {}
        self.fm.signal_bind('preview.cleared', lambda signal: self._clear_cache(signal.path))

    def _clear_cache(self, path):
        if os.path.exists(path):
            self.cache = {
                ce: cd
                for ce, cd in self.cache.items()
                if ce.inode != os.stat(path).st_ino
            }

    def _sixel_cache(self, path, width, height):
        stat = os.stat(path)
        cacheable = _CacheableSixelImage(width, height, stat.st_ino)

        if cacheable not in self.cache:
            font_width, font_height = get_font_dimensions()
            fit_width = font_width * width
            fit_height = font_height * height

            sixel_dithering = self.fm.settings.sixel_dithering
            cached = TemporaryFile("w+", prefix="ranger", suffix=path.replace(os.sep, "-"))

            environ = dict(os.environ)
            environ.setdefault("MAGICK_OCL_DEVICE", "true")
            try:
                check_call(
                    [
                        *MAGICK_CONVERT_CMD_BASE,
                        path + "[0]",
                        "-geometry",
                        "{0}x{1}>".format(fit_width, fit_height),
                        "-dither",
                        sixel_dithering,
                        "sixel:-",
                    ],
                    stdout=cached,
                    stderr=DEVNULL,
                    env=environ,
                )
            except CalledProcessError:
                raise ImageDisplayError("ImageMagick failed processing the SIXEL image")
            except FileNotFoundError:
                raise ImageDisplayError("SIXEL image previews require ImageMagick")
            finally:
                cached.flush()

            if os.fstat(cached.fileno()).st_size == 0:
                raise ImageDisplayError("ImageMagick produced an empty SIXEL image file")

            self.cache[cacheable] = _CachedSixelImage(mmap.mmap(cached.fileno(), 0), cached)

        return self.cache[cacheable].image

    def draw(self, path, start_x, start_y, width, height):
        if self.win is None:
            self.win = self.fm.ui.win.subwin(height, width, start_y, start_x)
        else:
            self.win.mvwin(start_y, start_x)
            self.win.resize(height, width)

        with temporarily_moved_cursor(start_y, start_x):
            sixel = self._sixel_cache(path, width, height)[:]
            if PY3:
                sys.stdout.buffer.write(sixel)
            else:
                sys.stdout.write(sixel)
            sys.stdout.flush()

    def clear(self, start_x, start_y, width, height):
        if self.win is not None:
            self.win.clear()
            self.win.refresh()

            self.win = None

        self.fm.ui.win.redrawwin()

    def quit(self):
        self.clear(0, 0, 0, 0)
        self.cache = {}


@register_image_displayer("terminology")
class TerminologyImageDisplayer(ImageDisplayer, FileManagerAware):
    """Implementation of ImageDisplayer using terminology image display support
    (https://github.com/billiob/terminology).

    Ranger must be running in terminology for this to work.
    Doesn't work with TMUX :/
    """

    def __init__(self):
        self.display_protocol = "\033"
        self.close_protocol = "\000"

    def draw(self, path, start_x, start_y, width, height):
        with temporarily_moved_cursor(start_y, start_x):
            # Write intent
            sys.stdout.write("%s}ic#%d;%d;%s%s" % (
                self.display_protocol,
                width, height,
                path,
                self.close_protocol))

            # Write Replacement commands ('#')
            for y in range(0, height):
                move_cur(start_y + y, start_x)
                sys.stdout.write("%s}ib%s%s%s}ie%s\n" % (  # needs a newline to work
                    self.display_protocol,
                    self.close_protocol,
                    "#" * width,
                    self.display_protocol,
                    self.close_protocol))

    def clear(self, start_x, start_y, width, height):
        self.fm.ui.win.redrawwin()
        self.fm.ui.win.refresh()

    def quit(self):
        self.clear(0, 0, 0, 0)


@register_image_displayer("urxvt")
class URXVTImageDisplayer(ImageDisplayer, FileManagerAware):
    """Implementation of ImageDisplayer working by setting the urxvt
    background image "under" the preview pane.

    Ranger must be running in urxvt for this to work.

    """

    def __init__(self):
        self.display_protocol = "\033"
        self.close_protocol = "\a"
        if os.environ["TERM"].startswith(("screen", "tmux")):
            self.display_protocol += "Ptmux;\033\033"
            self.close_protocol += "\033\\"
        self.display_protocol += "]20;"

    @staticmethod
    def _get_max_sizes():
        """Use the whole terminal."""
        pct_width = 100
        pct_height = 100
        return pct_width, pct_height

    @staticmethod
    def _get_centered_offsets():
        """Center the image."""
        pct_x = 50
        pct_y = 50
        return pct_x, pct_y

    def _get_sizes(self):
        """Return the width and height of the preview pane in relation to the
        whole terminal window.

        """
        if self.fm.ui.pager.visible:
            return self._get_max_sizes()

        total_columns_ratio = sum(self.fm.settings.column_ratios)
        preview_column_ratio = self.fm.settings.column_ratios[-1]
        pct_width = int((100 * preview_column_ratio) / total_columns_ratio)
        pct_height = 100  # As much as possible while preserving the aspect ratio.
        return pct_width, pct_height

    def _get_offsets(self):
        """Return the offsets of the image center."""
        if self.fm.ui.pager.visible:
            return self._get_centered_offsets()

        pct_x = 100  # Right-aligned.
        pct_y = 2    # TODO: Use the font size to calculate this offset.
        return pct_x, pct_y

    def draw(self, path, start_x, start_y, width, height):
        # The coordinates in the arguments are ignored as urxvt takes
        # the coordinates in a non-standard way: the position of the
        # image center as a percentage of the terminal size. As a
        # result all values below are in percents.

        pct_x, pct_y = self._get_offsets()
        pct_width, pct_height = self._get_sizes()

        sys.stdout.write(
            self.display_protocol
            + path
            + ";{pct_width}x{pct_height}+{pct_x}+{pct_y}:op=keep-aspect".format(
                pct_width=pct_width, pct_height=pct_height, pct_x=pct_x, pct_y=pct_y
            )
            + self.close_protocol
        )
        sys.stdout.flush()

    def clear(self, start_x, start_y, width, height):
        sys.stdout.write(
            self.display_protocol
            + ";100x100+1000+1000"
            + self.close_protocol
        )
        sys.stdout.flush()

    def quit(self):
        self.clear(0, 0, 0, 0)  # dummy assignments


@register_image_displayer("urxvt-full")
class URXVTImageFSDisplayer(URXVTImageDisplayer):
    """URXVTImageDisplayer that utilizes the whole terminal."""

    def _get_sizes(self):
        """Use the whole terminal."""
        return self._get_max_sizes()

    def _get_offsets(self):
        """Center the image."""
        return self._get_centered_offsets()


@register_image_displayer("kitty")
class KittyImageDisplayer(ImageDisplayer, FileManagerAware):
    """Implementation of ImageDisplayer for kitty (https://github.com/kovidgoyal/kitty/)
    terminal. It uses the built APC to send commands and data to kitty,
    which in turn renders the image. The APC takes the form
    '\033_Gk=v,k=v...;bbbbbbbbbbbbbb\033\\'
       |   ---------- --------------  |
    escape code  |             |    escape code
                 |  base64 encoded payload
        key: value pairs as parameters
    For more info please head over to :
        https://github.com/kovidgoyal/kitty/blob/master/graphics-protocol.asciidoc"""
    protocol_start = b'\x1b_G'
    protocol_end = b'\x1b\\'
    # we are going to use stdio in binary mode a lot, so due to py2 -> py3
    # differences is worth to do this:
    stdbout = getattr(sys.stdout, 'buffer', sys.stdout)
    stdbin = getattr(sys.stdin, 'buffer', sys.stdin)
    # counter for image ids on kitty's end
    image_id = 0
    # we need to find out the encoding for a path string, ascii won't cut it
    try:
        fsenc = sys.getfilesystemencoding()  # returns None if standard utf-8 is used
        # throws LookupError if can't find the codec, TypeError if fsenc is None
        codecs.lookup(fsenc)
    except (LookupError, TypeError):
        fsenc = 'utf-8'

    def __init__(self):
        # the rest of the initializations that require reading stdio or raising exceptions
        # are delayed to the first draw call, since curses
        # and ranger exception handler are not online at __init__() time
        self.needs_late_init = True
        # to init in _late_init()
        self.backend = None
        self.stream = None
        self.pix_row, self.pix_col = (0, 0)
        self.temp_file_dir = None  # Only used when streaming is not an option

    def _late_init(self):
        # tmux
        if 'kitty' not in os.environ['TERM']:
            # this doesn't seem to work, ranger freezes...
            # commenting out the response check does nothing
            # self.protocol_start = b'\033Ptmux;\033' + self.protocol_start
            # self.protocol_end += b'\033\\'
            raise ImgDisplayUnsupportedException(
                'kitty previews only work in'
                + ' kitty and outside tmux. '
                + 'Make sure your TERM contains the string "kitty"')

        # automatic check if we share the filesystem using a dummy file
        with NamedTemporaryFile() as tmpf:
            tmpf.write(bytearray([0xFF] * 3))
            tmpf.flush()
            for cmd in self._format_cmd_str(
                    {'a': 'q', 'i': 1, 'f': 24, 't': 'f', 's': 1, 'v': 1, 'S': 3},
                    payload=base64.standard_b64encode(tmpf.name.encode(self.fsenc))):
                self.stdbout.write(cmd)
            sys.stdout.flush()
            resp = b''
            while resp[-2:] != self.protocol_end:
                resp += self.stdbin.read(1)
        # set the transfer method based on the response
        # if resp.find(b'OK') != -1:
        if b'OK' in resp:
            self.stream = False
            self.temp_file_dir = os.path.join(
                gettempdir(), "tty-graphics-protocol"
            )
            try:
                os.mkdir(self.temp_file_dir)
            except OSError:
                # COMPAT: Python 2.7 does not define FileExistsError so we have
                # to check whether the problem is the directory already being
                # present. This is prone to race conditions, TOCTOU.
                if not os.path.isdir(self.temp_file_dir):
                    raise ImgDisplayUnsupportedException(
                        "Could not create temporary directory for previews : {d}".format(
                            d=self.temp_file_dir
                        )
                    )
        elif b'EBADF' in resp:
            self.stream = True
        else:
            raise ImgDisplayUnsupportedException(
                'kitty replied an unexpected response: {r}'.format(r=resp))

        # get the image manipulation backend
        try:
            # pillow is the default since we are not going
            # to spawn other processes, so it _should_ be faster
            import PIL.Image
            self.backend = PIL.Image
        except ImportError:
            raise ImageDisplayError("Image previews in kitty require PIL (pillow)")
            # TODO: implement a wrapper class for Imagemagick process to
            # replicate the functionality we use from im

        # get dimensions of a cell in pixels
        ret = fcntl.ioctl(sys.stdout, termios.TIOCGWINSZ,
                          struct.pack('HHHH', 0, 0, 0, 0))
        n_cols, n_rows, x_px_tot, y_px_tot = struct.unpack('HHHH', ret)
        self.pix_row, self.pix_col = x_px_tot // n_rows, y_px_tot // n_cols
        self.needs_late_init = False

    def draw(self, path, start_x, start_y, width, height):
        self.image_id += 1
        # dictionary to store the command arguments for kitty
        # a is the display command, with T going for immediate output
        # i is the id entifier for the image
        cmds = {'a': 'T', 'i': self.image_id}
        # sys.stderr.write('{0}-{1}@{2}x{3}\t'.format(
        #     start_x, start_y, width, height))

        # finish initialization if it is the first call
        if self.needs_late_init:
            self._late_init()

        with warnings.catch_warnings(record=True):  # as warn:
            warnings.simplefilter('ignore', self.backend.DecompressionBombWarning)
            image = self.backend.open(path)
            # TODO: find a way to send a message to the user that
            # doesn't stop the image from displaying
            # if warn:
            #     raise ImageDisplayError(str(warn[-1].message))
        box = (width * self.pix_row, height * self.pix_col)

        if image.width > box[0] or image.height > box[1]:
            scale = min(box[0] / image.width, box[1] / image.height)
            image = image.resize((int(scale * image.width), int(scale * image.height)),
                                 self.backend.LANCZOS)

        if image.mode not in ("RGB", "RGBA"):
            image = image.convert(
                "RGBA" if "transparency" in image.info else "RGB"
            )
        # start_x += ((box[0] - image.width) // 2) // self.pix_row
        # start_y += ((box[1] - image.height) // 2) // self.pix_col
        if self.stream:
            # encode the whole image as base64
            # TODO: implement z compression
            # to possibly increase resolution in sent image
            # t: transmissium medium, 'd' for embedded
            # f: size of a pixel fragment (8bytes per color)
            # s, v: size of the image to recompose the flattened data
            # c, r: size in cells of the viewbox
            cmds.update({'t': 'd', 'f': len(image.getbands()) * 8,
                         's': image.width, 'v': image.height, })
            payload = base64.standard_b64encode(
                bytearray().join(map(bytes, image.getdata())))
        else:
            # put the image in a temporary png file
            # t: transmissium medium, 't' for temporary file (kitty will delete it for us)
            # f: size of a pixel fragment (100 just mean that the file is png encoded,
            #       the only format except raw RGB(A) bitmap that kitty understand)
            # c, r: size in cells of the viewbox
            cmds.update({'t': 't', 'f': 100, })
            with NamedTemporaryFile(
                prefix='ranger_thumb_',
                suffix='.png',
                dir=self.temp_file_dir,
                delete=False,
            ) as tmpf:
                image.save(tmpf, format='png', compress_level=0)
                payload = base64.standard_b64encode(tmpf.name.encode(self.fsenc))

        with temporarily_moved_cursor(int(start_y), int(start_x)):
            for cmd_str in self._format_cmd_str(cmds, payload=payload):
                self.stdbout.write(cmd_str)
        # catch kitty answer before the escape codes corrupt the console
        resp = b''
        while resp[-2:] != self.protocol_end:
            resp += self.stdbin.read(1)
        if b'OK' in resp:
            return
        else:
            raise ImageDisplayError('kitty replied "{r}"'.format(r=resp))

    def clear(self, start_x, start_y, width, height):
        # let's assume that every time ranger call this
        # it actually wants just to remove the previous image
        # TODO: implement this using the actual x, y, since the protocol
        #       supports it
        cmds = {'a': 'd', 'i': self.image_id}
        for cmd_str in self._format_cmd_str(cmds):
            self.stdbout.write(cmd_str)
        self.stdbout.flush()
        # kitty doesn't seem to reply on deletes, checking like we do in draw()
        # will slows down scrolling with timeouts from select
        self.image_id = max(0, self.image_id - 1)
        self.fm.ui.win.redrawwin()
        self.fm.ui.win.refresh()

    def _format_cmd_str(self, cmd, payload=None, max_slice_len=2048):
        central_blk = ','.join(["{k}={v}".format(k=k, v=v)
                                for k, v in cmd.items()]).encode('ascii')
        if payload is not None:
            # we add the m key to signal a multiframe communication
            # appending the end (m=0) key to a single message has no effect
            while len(payload) > max_slice_len:
                payload_blk, payload = payload[:max_slice_len], payload[max_slice_len:]
                yield self.protocol_start + \
                    central_blk + b',m=1;' + payload_blk + \
                    self.protocol_end
            yield self.protocol_start + \
                central_blk + b',m=0;' + payload + \
                self.protocol_end
        else:
            yield self.protocol_start + central_blk + b';' + self.protocol_end

    def quit(self):
        # clear all remaining images, then check if all files went through or
        # are orphaned
        while self.image_id >= 1:
            self.clear(0, 0, 0, 0)
        # for k in self.temp_paths:
        #     try:
        #         os.remove(self.temp_paths[k])
        #     except (OSError, IOError):
        #         continue


@register_image_displayer("ueberzug")
class UeberzugImageDisplayer(ImageDisplayer):
    """Implementation of ImageDisplayer using ueberzug.
    Ueberzug can display images in a Xorg session.
    Does not work over ssh.
    """
    IMAGE_ID = 'preview'
    is_initialized = False

    def __init__(self):
        self.process = None

    def initialize(self):
        """start ueberzug"""
        if (self.is_initialized and self.process.poll() is None
                and not self.process.stdin.closed):
            return

        # We cannot close the process because that stops the preview.
        # pylint: disable=consider-using-with
        with open(os.devnull, "wb") as devnull:
            self.process = Popen(
                ["ueberzug", "layer", "--silent"],
                cwd=self.working_dir,
                stderr=devnull,
                stdin=PIPE,
                universal_newlines=True,
            )
        self.is_initialized = True

    def _execute(self, **kwargs):
        self.initialize()
        self.process.stdin.write(json.dumps(kwargs) + '\n')
        self.process.stdin.flush()

    def draw(self, path, start_x, start_y, width, height):
        self._execute(
            action='add',
            identifier=self.IMAGE_ID,
            x=start_x,
            y=start_y,
            max_width=width,
            max_height=height,
            path=path
        )

    def clear(self, start_x, start_y, width, height):
        if self.process and not self.process.stdin.closed:
            self._execute(action='remove', identifier=self.IMAGE_ID)

    def quit(self):
        if self.is_initialized and self.process.poll() is None:
            timer_kill = threading.Timer(1, self.process.kill, [])
            try:
                self.process.terminate()
                timer_kill.start()
                self.process.communicate()
            finally:
                timer_kill.cancel()
