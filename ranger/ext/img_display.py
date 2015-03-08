# This software is distributed under the terms of the GNU GPL version 3.
"""Interface for drawing images into the console

This module provides functions to draw images in the terminal using supported
implementations, which are currently w3m and iTerm2.
"""

import base64
import curses
import fcntl
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

class ITerm2ImageDisplayer(ImageDisplayer, FileManagerAware):
    """Implementation of ImageDisplayer using iTerm2 image display support
    (http://iterm2.com/images.html).

    Ranger must be running in iTerm2 for this to work.
    """
    def draw(self, path, start_x, start_y, width, height):
        curses.putp(curses.tigetstr("sc"))
        sys.stdout.write(curses.tparm(curses.tigetstr("cup"), start_y, start_x))
        sys.stdout.write(self._generate_iterm2_input(path, width, height))
        curses.putp(curses.tigetstr("rc"))
        sys.stdout.flush()

    def clear(self, start_x, start_y, width, height):
        self.fm.ui.win.redrawwin()
        self.fm.ui.win.refresh()

    def _generate_iterm2_input(self, path, width, height):
        """Prepare the image content of path for image display in iTerm2"""
        content = self._encode_image_content(path)
        text = "\033]1337;File=inline=1;preserveAspectRatio=0"
        text += ";size=" + str(len(content))
        text += ";width=" + str(width)
        text += ":" + content
        text += "\a\n"
        return text

    def _encode_image_content(self, path):
        """Read and encode the contents of path"""
        file = open(path, "r")
        try:
            return base64.b64encode(file.read())
        except:
            return ""
        finally:
            file.close()

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
