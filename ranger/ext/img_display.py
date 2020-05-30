# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# Author: Emanuel Guevel, 2013
# Author: Delisa Mason, 2015

"""Interface for drawing images into the console

This module provides functions to draw images in the terminal using supported
implementations, which are currently w3m, iTerm2 and urxvt.
"""

from __future__ import (absolute_import, division, print_function)

import base64
import curses
import errno
import fcntl
import imghdr
import os
import struct
import sys
import warnings
import json
import threading
from subprocess import Popen, PIPE
from collections import defaultdict

import termios
import codecs
from tempfile import NamedTemporaryFile

from ranger.core.shared import FileManagerAware

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


class SavedCursor(object):
    """ Context manager that saves the position of the cursor
    and restores it at the end of the with block.
    While inside the block the cursor can be moved by calling the move method"""
    stdbout = getattr(sys.stdout, 'buffer', sys.stdout)

    def __enter__(self):
        self.stdbout.write(curses.tigetstr("sc"))
        self.stdbout.flush()
        return self

    def __exit__(self, ex_type, ex_value, traceback):
        self.stdbout.write(curses.tigetstr("rc"))
        self.stdbout.flush()

    def move(self, to_x, to_y):
        tparm = curses.tparm(curses.tigetstr("cup"), to_y, to_x)
        self.stdbout.write(tparm)
        self.stdbout.flush()


def get_cell_pixel_size():
    """ Returns the size of a cell in pixels as a tuple (width, height)"""
    ret = fcntl.ioctl(sys.stdout, termios.TIOCGWINSZ,
                      struct.pack('HHHH', 0, 0, 0, 0))
    return struct.unpack('HHHH', ret)


def best_rect_fit(max_rect, fit_rect, start_pos):
    """ Returns a rectangle contained within max_rect
        that mantains the aspect ratio of fit_rect.
        start_pos is transformed so that if it was the position
        of the top leftmost corner of max_rect it now points
        to the coordinates that center fit_rect inside max_rect"""
    if fit_rect[0] > max_rect[0] or fit_rect[1] > max_rect[1]:
        scale = min(max_rect[0] / fit_rect[0], max_rect[1] / fit_rect[1])
        ret_rect = (fit_rect[0] * scale, fit_rect[1] * scale)
    else:
        ret_rect = fit_rect

    ret_pos = (start_pos[0] + ((max_rect[0] - ret_rect[0]) / 2),
               start_pos[1] + ((max_rect[1] - ret_rect[1]) / 2))

    return ret_rect, ret_pos


class ImageDisplayError(Exception):
    pass


class ImgDisplayUnsupportedException(Exception):
    pass


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
        pass

    def clear(self, start_x, start_y, width, height):
        """Clear a part of terminal display."""
        pass

    def quit(self):
        """Cleanup and close"""
        pass


@register_image_displayer("w3m")
class W3MImageDisplayer(ImageDisplayer, FileManagerAware):
    """Implementation of ImageDisplayer using w3mimgdisplay, an utilitary
    program from w3m (a text-based web browser). w3mimgdisplay can display
    images either in virtual tty (using linux framebuffer) or in a Xorg session.
    Does not work over ssh.

    w3m need to be installed for this to work.
    """

    def __init__(self):
        self.binary_path = None
        self.process = None
        self.pix_row, self.pix_col = (0, 0)
        self.is_initialized = False

    def initialize(self):
        """start w3mimgdisplay"""
        self.binary_path = self._find_w3mimgdisplay_executable()  # may crash
        self.process = Popen([self.binary_path] + W3MIMGDISPLAY_OPTIONS, cwd=self.working_dir,
                             stdin=PIPE, stdout=PIPE, universal_newlines=True)

        # get the font dimensions
        # Some terminals might return 0, 0, so let's check for that
        # and try to salvage it using w3m
        n_cols, n_rows, x_px_tot, y_px_tot = get_cell_pixel_size()
        if x_px_tot == 0 and y_px_tot == 0:
            process = Popen([self.binary_path, "-test"], stdout=PIPE, universal_newlines=True)
            output, _ = process.communicate()
            output = output.split()
            # adjust for misplacement
            x_px_tot, y_px_tot = int(output[0]) + 2, int(output[1]) + 2
        self.pix_row, self.pix_col = x_px_tot / n_rows, y_px_tot / n_cols
        # if after this the size is still zero abort
        if self.pix_row == 0 or self.pix_col == 0:
            raise ImgDisplayUnsupportedException
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

    def _generate_w3m_input(self, path, x, y, width, height):
        # get image size
        height *= self.pix_col
        width *= self.pix_row
        y *= self.pix_col
        x *= self.pix_row
        if path is not None:
            cmd = "5;{}\n".format(path)
            self.process.stdin.write(cmd)
            self.process.stdin.flush()
            output = self.process.stdout.readline().split()
            if len(output) != 2:
                raise ImageDisplayError('Failed to execute w3mimgdisplay: {}'.format(output))
            else:
                width_i = int(output[0])
                height_i = int(output[1])
            (width, height), (x, y) = best_rect_fit((width, height),
                                                    (width_i, height_i),
                                                    (x, y))
        return "{cmd};{x};{y};{w};{h};;;;;{path}\n4;\n3;\n".format(
            cmd=(6 if path is None else "0;1"),
            path=("" if path is None else path),
            x=int(x + 0.5),
            y=int(y),
            w=int(width + 0.4),
            h=int(height))

    def draw(self, path, start_x, start_y, width, height):
        if not self.is_initialized or self.process.poll() is not None:
            self.initialize()
        cmd = self._generate_w3m_input(path, start_x, start_y, width, height)

        # Mitigate the issue with the horizontal black bars when
        # selecting some images on some systems. 2 milliseconds seems
        # enough. Adjust as necessary.
        if self.fm.settings.w3m_delay > 0:
            from time import sleep
            sleep(self.fm.settings.w3m_delay)

        self.process.stdin.write(cmd)
        self.process.stdin.flush()
        self.process.stdout.readline()
        # self.quit()
        # self.is_initialized = False

    def clear(self, start_x, start_y, width, height):
        if not self.is_initialized or self.process.poll() is not None:
            self.initialize()

        # cmd = "6;{x};{y};{w};{h}\n4;\n3;\n".format(
        #     x=int((start_x - 0.5) * self.pix_row),
        #     y=int(start_y * self.pix_col),
        #     # y = int((start_y + 1) * fonth), # (for tmux top status bar)
        #     w=int((width + 0.4) * self.pix_row),
        #     h=int(height * self.pix_col + 2),
        #     # h = (height - 1) * fonth + 1, # (for tmux top status bar)
        # )

        cmd = self._generate_w3m_input(None, start_x, start_y, width, height)

        try:
            self.fm.ui.win.redrawwin()
            self.process.stdin.write(cmd)
        except IOError as ex:
            if ex.errno == errno.EPIPE:
                return
            raise
        self.process.stdin.flush()
        self.process.stdout.readline()

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
        width *= self.fm.settings.iterm2_font_width
        height *= self.fm.settings.iterm2_font_height

        width_i, height_i = self._get_image_dimensions(path)
        (width, _), _ = best_rect_fit((width, height),
                                      (width_i, height_i),
                                      (start_x, start_y))

        with SavedCursor() as saved_c:
            saved_c.move(start_x, start_y)
            sys.stdout.write(self._generate_iterm2_input(path, width))

    def clear(self, start_x, start_y, width, height):
        self.fm.ui.win.redrawwin()
        self.fm.ui.win.refresh()

    def quit(self):
        self.clear(0, 0, 0, 0)

    def _generate_iterm2_input(self, path, image_width):
        """Prepare the image content of path for image display in iTerm2"""
        content = self._encode_image_content(path)
        display_protocol = "\033"
        close_protocol = "\a"
        if "screen" in os.environ['TERM']:
            display_protocol += "Ptmux;\033\033"
            close_protocol += "\033\\"

        return "{0}]1337;File=inline=1;preserveAspectRatio=0;size={1};width={2}px:{3}{4}\n".format(
            display_protocol,
            str(len(content)),
            str(int(image_width)),
            content,
            close_protocol)

    @staticmethod
    def _encode_image_content(path):
        """Read and encode the contents of path"""
        with open(path, 'rb') as fobj:
            return base64.b64encode(fobj.read()).decode('utf-8')

    @staticmethod
    def _get_image_dimensions(path):
        """Determine image size using imghdr"""
        file_handle = open(path, 'rb')
        file_header = file_handle.read(24)
        image_type = imghdr.what(path)
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
        else:
            file_handle.close()
            raise TypeError("FileType not supported")
        file_handle.close()
        return width, height


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
        with SavedCursor() as saved_c:
            saved_c.move(start_x, start_y)
            # Write intent
            sys.stdout.write("%s}ic#%d;%d;%s%s" % (
                self.display_protocol,
                width, height,
                path,
                self.close_protocol))

            # Write Replacement commands ('#')
            for y in range(0, height):
                saved_c.move(start_x, start_y + y)
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
        if "screen" in os.environ['TERM']:
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
    # differnces is worth to do this:
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
        self.tmpdir = os.getenv('XDG_RUNTIME_DIR', '/tmp') + os.sep + 'ranger_thumb'
        if not os.path.exists(self.tmpdir):
            os.makedirs(self.tmpdir)

        if 'kitty' not in os.environ['TERM']:
            raise ImgDisplayUnsupportedException(
                'kitty previews only work in'
                + ' kitty and outside tmux. '
                + 'Make sure your TERM contains the string "kitty"')

    def _late_init(self):
        # automatic check if we share the filesystem using a dummy file
        with NamedTemporaryFile(delete=False) as tmpf:
            tmpf.write(bytearray([0xFF] * 3))
            tmpf.flush()
            for cmd in self._format_cmd_str(
                    {'a': 'q', 'i': 1, 'f': 24, 't': 't', 's': 1, 'v': 1, 'S': 3},
                    payload=base64.standard_b64encode(tmpf.name.encode(self.fsenc))):
                self.stdbout.write(cmd)
            sys.stdout.flush()
            resp = b''
            while resp[-2:] != self.protocol_end:
                resp += self.stdbin.read(1)
        # set the transfer method based on the response
        if b'OK' in resp:
            self.stream = False
        elif b'EBADF' in resp:
            self.stream = True
        else:
            raise ImgDisplayUnsupportedException(
                'kitty replied an unexpected response: {}'.format(resp))

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
        n_cols, n_rows, x_px_tot, y_px_tot = get_cell_pixel_size()
        self.pix_row, self.pix_col = x_px_tot / n_rows, y_px_tot / n_cols
        self.needs_late_init = False

    def draw(self, path, start_x, start_y, width, height):  # pylint: disable=too-many-locals
        self.image_id += 1
        # dictionary to store the command arguments for kitty
        # a is the display command, with T going for immediate output
        # i is the id entifier for the image
        cmds = {'a': 'T', 'i': self.image_id}
        # sys.stderr.write('{}-{}@{}x{}\t'.format(start_x, start_y, width, height))

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
        box, pos = best_rect_fit((width * self.pix_row, height * self.pix_col),
                                 (image.width, image.height),
                                 (start_x * self.pix_row, start_y * self.pix_col))
        image = image.resize([int(c) for c in box], self.backend.LANCZOS)

        if image.mode != 'RGB' and image.mode != 'RGBA':
            image = image.convert('RGB')
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
            cmds.update({'t': 'f', 'f': 100, })
            # with NamedTemporaryFile(prefix='ranger_thumb_', suffix='.png', delete=False) as tmpf:
            with open(self.tmpdir + os.sep + 'thumb.png', 'wb') as tmpf:
                image.save(tmpf, format='png', compress_level=0)
                payload = base64.standard_b64encode(tmpf.name.encode(self.fsenc))

        with SavedCursor() as saved_c:
            saved_c.move(int(pos[0] / self.pix_row), int(pos[1] / self.pix_col))
            for cmd_str in self._format_cmd_str(cmds, payload=payload):
                self.stdbout.write(cmd_str)
        # catch kitty answer before the escape codes corrupt the console
        resp = b''
        while resp[-2:] != self.protocol_end:
            resp += self.stdbin.read(1)
        if b'OK' not in resp:
            raise ImageDisplayError('kitty replied "{}"'.format(resp))

    def clear(self, start_x, start_y, width, height):
        # let's assume that every time ranger call this
        # it actually wants just to remove the previous image
        # TODO: implement this using the actual x, y, since the protocol supports it
        cmds = {'a': 'd', 'i': self.image_id}
        for cmd_str in self._format_cmd_str(cmds):
            self.stdbout.write(cmd_str)
        self.stdbout.flush()
        # kitty doesn't seem to reply on deletes, checking like we do in draw()
        # will slows down scrolling with timeouts from select
        self.image_id -= 1
        self.fm.ui.win.redrawwin()
        self.fm.ui.win.refresh()

    def _format_cmd_str(self, cmd, payload=None, max_slice_len=2048):
        central_blk = ','.join(["{}={}".format(k, v) for k, v in cmd.items()]).encode('ascii')
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
        # clear all remaining images, then check if all files went through or are orphaned
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

        self.process = Popen(['ueberzug', 'layer', '--silent'], cwd=self.working_dir,
                             stdin=PIPE, universal_newlines=True)
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
