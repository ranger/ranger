# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# Author: Emanuel Guevel, 2013
# Author: Delisa Mason, 2015

"""Interface for drawing images into the console

This module provides functions to draw images in the terminal using supported
implementations, which are currently w3m and iTerm2.
"""

import base64
import curses
import fcntl
import imghdr
import os
import select
import struct
import sys
import termios
from ranger.core.shared import FileManagerAware
from subprocess import Popen, PIPE

W3MIMGDISPLAY_PATH = '/usr/lib/w3m/w3mimgdisplay'
W3MIMGDISPLAY_OPTIONS = []

class ImgDisplayUnsupportedException(Exception):
    pass

class ImageDisplayer(object):
    """Image display provider functions for drawing images in the terminal"""
    def draw(self, path, start_x, start_y, width, height):
        """Draw an image at the given coordinates."""
        pass

    def clear(self, start_x, start_y, width, height):
        """Clear a part of terminal display."""
        pass

    def quit(self):
        """Cleanup and close"""
        pass

class W3MImageDisplayer(ImageDisplayer):
    """Implementation of ImageDisplayer using w3mimgdisplay, an utilitary
    program from w3m (a text-based web browser). w3mimgdisplay can display
    images either in virtual tty (using linux framebuffer) or in a Xorg session.
    Does not work over ssh.

    w3m need to be installed for this to work.
    """
    is_initialized = False

    def initialize(self):
        """start w3mimgdisplay"""
        self.binary_path = os.environ.get("W3MIMGDISPLAY_PATH", None)
        if not self.binary_path:
            self.binary_path = W3MIMGDISPLAY_PATH
        self.process = Popen([self.binary_path] + W3MIMGDISPLAY_OPTIONS,
                stdin=PIPE, stdout=PIPE, universal_newlines=True)
        self.is_initialized = True

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

        fontw, fonth = _get_font_dimensions()

        cmd = "6;{x};{y};{w};{h}\n4;\n3;\n".format(
                x = int((start_x - 0.2) * fontw),
                y = start_y * fonth,
                # y = int((start_y + 1) * fonth), # (for tmux top status bar)
                w = int((width + 0.4) * fontw),
                h = height * fonth + 1)
                # h = (height - 1) * fonth + 1) # (for tmux top status bar)

        self.process.stdin.write(cmd)
        self.process.stdin.flush()
        self.process.stdout.readline()

    def _generate_w3m_input(self, path, start_x, start_y, max_width, max_height):
        """Prepare the input string for w3mimgpreview

        start_x, start_y, max_height and max_width specify the drawing area.
        They are expressed in number of characters.
        """
        fontw, fonth = _get_font_dimensions()
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
                x = int((start_x - 0.2) * fontw),
                y = start_y * fonth,
                # y = (start_y + 1) * fonth, # (for tmux top status bar)
                w = width,
                h = height,
                filename = path)

    def quit(self):
        if self.is_initialized:
            self.process.kill()

class ITerm2ImageDisplayer(ImageDisplayer, FileManagerAware):
    """Implementation of ImageDisplayer using iTerm2 image display support
    (http://iterm2.com/images.html).

    Ranger must be running in iTerm2 for this to work.
    """
    _minimum_font_width = 8
    _minimum_font_height = 11

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
        text = "\033]1337;File=inline=1;preserveAspectRatio=0;"
        text += "size={0};width={1}px:{2}\a\n".format(
            str(len(content)),
            str(int(image_width)),
            content)
        return text

    def _fit_width(self, width, height, max_cols, max_rows):
        max_width = self._minimum_font_width * max_cols
        max_height = self._minimum_font_height * max_rows
        if height > max_height:
            if width > max_width:
                width_scale = max_width/float(width)
                height_scale = max_height/float(height)
                min_scale = min(width_scale, height_scale)
                max_scale = max(width_scale, height_scale)
                if width * max_scale <= max_width and height * max_scale <= max_height:
                    return (width * max_scale)
                else:
                    return (width * min_scale)
            else:
                scale = max_height/float(height)
                return (width * scale)
        elif width > max_width:
            scale = max_width/float(width)
            return (width * scale)
        else:
            return width


    def _encode_image_content(self, path):
        """Read and encode the contents of path"""
        file = open(path, 'rb')
        try:
            return base64.b64encode(file.read())
        except:
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
            except:
                file_handle.close()
                return 0, 0
        else:
            file_handle.close()
            return 0, 0
        file_handle.close()
        return width, height

def _get_font_dimensions():
    # Get the height and width of a character displayed in the terminal in
    # pixels.
    s = struct.pack("HHHH", 0, 0, 0, 0)
    fd_stdout = sys.stdout.fileno()
    x = fcntl.ioctl(fd_stdout, termios.TIOCGWINSZ, s)
    rows, cols, xpixels, ypixels = struct.unpack("HHHH", x)
    if xpixels == 0 and ypixels == 0:
        binary_path = os.environ.get("W3MIMGDISPLAY_PATH", None)
        if not binary_path:
            binary_path = W3MIMGDISPLAY_PATH
        process = Popen([binary_path, "-test"],
            stdout=PIPE, universal_newlines=True)
        output, _ = process.communicate()
        output = output.split()
        xpixels, ypixels = int(output[0]), int(output[1])
        # adjust for misplacement
        xpixels += 2
        ypixels += 2

    return (xpixels // cols), (ypixels // rows)
