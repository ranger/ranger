# This software is distributed under the terms of the GNU GPL version 3.

"""Interface for w3mimgdisplay to draw images into the console

This module provides functions to draw images in the terminal using
w3mimgdisplay, an utilitary program from w3m (a text-based web browser).
w3mimgdisplay can display images either in virtual tty (using linux
framebuffer) or in a Xorg session.

w3m need to be installed for this to work.
"""

import fcntl
import os
import select
import struct
import sys
import termios
from subprocess import Popen, PIPE

W3MIMGDISPLAY_PATH = '/usr/lib/w3m/w3mimgdisplay'
W3MIMGDISPLAY_OPTIONS = []

class ImgDisplayUnsupportedException(Exception):
    pass


class ImageDisplayer(object):
    is_initialized = False

    def initialize(self):
        """start w3mimgdisplay"""
        self.is_initialized = True
        self.binary_path = os.environ.get("W3MIMGDISPLAY_PATH", None)
        if not self.binary_path:
            self.binary_path = W3MIMGDISPLAY_PATH
        self.process = Popen([self.binary_path] + W3MIMGDISPLAY_OPTIONS,
                stdin=PIPE, stdout=PIPE, universal_newlines=True)

    def draw(self, path, start_x, start_y, width, height):
        """Draw an image at the given coordinates."""
        if not self.is_initialized or self.process.poll() is not None:
            self.initialize()
        self.process.stdin.write(self._generate_w3m_input(path, start_x,
            start_y, width, height))
        self.process.stdin.flush()
        self.process.stdout.readline()

    def clear(self, start_x, start_y, width, height):
        """Clear a part of terminal display."""
        if not self.is_initialized or self.process.poll() is not None:
            self.initialize()

        fontw, fonth = _get_font_dimensions()

        cmd = "6;{x};{y};{w};{h}\n4;\n3;\n".format(
                x = start_x * fontw,
                y = start_y * fonth,
                w = (width + 1) * fontw,
                h = height * fonth)

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
        max_height_pixels = max_height * fonth

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
                x = start_x * fontw,
                y = start_y * fonth,
                w = width,
                h = height,
                filename = path)

    def quit(self):
        if self.is_initialized:
            self.process.kill()


def _get_font_dimensions():
    # Get the height and width of a character displayed in the terminal in
    # pixels.
    s = struct.pack("HHHH", 0, 0, 0, 0)
    fd_stdout = sys.stdout.fileno()
    x = fcntl.ioctl(fd_stdout, termios.TIOCGWINSZ, s)
    rows, cols, xpixels, ypixels = struct.unpack("HHHH", x)

    return (xpixels // cols), (ypixels // rows)
